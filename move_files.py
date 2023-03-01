import mpi4py.MPI as MPI
import os,sys,time,mmap
import argparse,logging,json
logger = logging.getLogger(__name__)
start_time = time.time()

comm = MPI.COMM_WORLD
rank = comm.Get_rank()
nranks = comm.Get_size()

## get local rank number per node
local_comm = comm.Split_type(MPI.COMM_TYPE_SHARED,0)
local_rank = local_comm.Get_rank()
local_nranks = local_comm.Get_size()

## build a comm that only includes first local rank from each node
# color = MPI.UNDEFINED
# if local_rank == 0:
#    color = 0
# one_per_node_comm = comm.Split(color,rank)
# one_rank = -1
# if one_per_node_comm != MPI.COMM_NULL:
#    one_rank = one_per_node_comm.Get_rank()
# one_nranks = -1
# if one_per_node_comm != MPI.COMM_NULL:
#    one_nranks = one_per_node_comm.Get_size()



def send_file(comm,source_filename,destination_filename,source_rank):
   rank = comm.Get_rank()
   
   logger.debug('broadcasting %s from rank %d to all ranks at %s',source_filename,source_rank,destination_filename)
   if rank == source_rank:
      logger.debug('source_rank')
      with open(source_filename,mode='rb') as file_handle:
         file_content = file_handle.read()
         
         # source rank also needs to copy files
         bytes_written = open(destination_filename,mode='wb').write(file_content)
         logger.debug('file size written: %d',bytes_written)
         
         # file_size = sys.getsizeof(file_content)
         comm.bcast(bytes_written,source_rank)
         logger.debug('sent file size in bytes: %d',bytes_written)
         comm.Bcast([file_content,bytes_written,MPI.BYTE],source_rank)
         logger.debug('sent file content')
      logger.debug('end if send file')
   else:
      logger.debug('receiver rank')
      file_size = None
      file_size = comm.bcast(file_size,source_rank)
      logger.debug('recv file size %d',file_size)
      sys.stdout.flush()
      file_content = mmap.mmap(-1,file_size)
      comm.Bcast([file_content,file_size,MPI.BYTE],source_rank)
      bytes_written = open(destination_filename,mode='wb').write(file_content.read())
      logger.debug('recv file size written: %d',bytes_written)
   logger.debug('done send file')


def main():
   ''' simple starter program that can be copied for use when starting a new script. '''
   logging_format = '%(asctime)s %(levelname)s:' + ('%05d' % rank) + ':%(name)s:%(message)s'
   logging_datefmt = '%Y-%m-%d %H:%M:%S'
   logging_level = logging.INFO
   
   parser = argparse.ArgumentParser(description='')
   parser.add_argument('-f','--file',help='name of file to copy, can list multiple.',required=True,action='append')
   parser.add_argument('-d','--destination',help='location for ranks to store files, this is typically the ram disk area',required=True)
   parser.add_argument('-j','--json-file',help='location for rank zero to output combined stats information in json format',required=True)
   parser.add_argument('-s','--source-rank',help='which rank will handle File IO',default=0,type=int)

   parser.add_argument('--debug', dest='debug', default=False, action='store_true', help="Set Logger to DEBUG")
   parser.add_argument('--error', dest='error', default=False, action='store_true', help="Set Logger to ERROR")
   parser.add_argument('--warning', dest='warning', default=False, action='store_true', help="Set Logger to ERROR")
   parser.add_argument('--logfilename',dest='logfilename',default=None,help='if set, logging information will go to file')
   args = parser.parse_args()

   if args.debug and not args.error and not args.warning:
      logging_level = logging.DEBUG
   elif not args.debug and args.error and not args.warning:
      logging_level = logging.ERROR
   elif not args.debug and not args.error and args.warning:
      logging_level = logging.WARNING

   logging.basicConfig(level=logging_level,
                       format=logging_format,
                       datefmt=logging_datefmt,
                       filename=args.logfilename)
   

   logger.debug('%d of %d   local: %d of %d',rank,nranks,local_rank,local_nranks)
   destination = os.path.join(args.destination,'%02d' % local_rank)
   os.makedirs(destination,exist_ok=True)
   logger.info('preparing to transfer %d files to %s reading from rank %d',len(args.file),args.destination,args.source_rank)
   for i,filename in enumerate(args.file):
      destination_filename = os.path.join(destination,os.path.basename(filename))
      send_file(comm,filename,destination_filename,args.source_rank)
      logger.debug('done with file %d : %s',i,filename)
   logger.debug('at barrier')
   comm.barrier()
   if rank == 0:
      end_time = time.time()
      duration = end_time - start_time
      logger.debug('runtime: %f',duration)
      json.dump({'combined':{'move_files_runtime':duration},'ranks':[]},open(args.json_file,'w'),indent=3,sort_keys=True)
   

   
if __name__ == '__main__':
   main()
