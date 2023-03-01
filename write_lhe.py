import mpi4py.MPI as MPI
import os,sys,time,json
import argparse,logging
logger = logging.getLogger(__name__)
start_time = time.time()
comm = MPI.COMM_WORLD
rank = comm.Get_rank()
nranks = comm.Get_size()
local_comm = comm.Split_type(MPI.COMM_TYPE_SHARED,0)
local_rank = local_comm.Get_rank()
local_nranks = local_comm.Get_size()


def calc_starting_point(sizes,rank):
   offset = 0
   for i in range(rank):
      offset = offset + sizes[i]
   return offset

def main():
   ''' MPI program to read LHE files from different ranks and write them to a shared output file. '''
   logging_format = '%(asctime)s %(levelname)s:' + ('%05d' % rank) + ':%(name)s:%(message)s'
   logging_datefmt = '%Y-%m-%d %H:%M:%S'
   logging_level = logging.INFO
   
   parser = argparse.ArgumentParser(description='MPI program to read LHE files from different ranks and write them to a shared output file')
   parser.add_argument('-i','--input',help='name of local LHE file.',required=True)
   parser.add_argument('-o','--output',help='output filename for the combined LHE file',required=True)
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

   logger.debug('opening file %s',args.input)
   # every rank should read their local file from RAM disk
   with open(args.input,mode='rb') as file_handle:
      # read LHE file
      file_content = file_handle.read()
   # determine size read from RAM disk
   file_size = len(file_content)
   logger.debug('read bytes: %d',file_size)
   # every rank needs to know the size of everyone elses data
   # do an all gather to share our size information
   all_file_sizes = comm.allgather(file_size)
   logger.debug('sent size of bytes: %d',file_size)
   # now calculate the bytes offset in the file
   offset = calc_starting_point(all_file_sizes,rank)
   logger.debug('offset = %d',offset)

   # now we open a file for writing
   logger.debug('writing to file: %s',args.output)
   mpi_file_handle = MPI.File.Open(comm,args.output, MPI.MODE_WRONLY | MPI.MODE_CREATE)
   mpi_file_handle.Write_at_all(offset,file_content)
   mpi_file_handle.Close()

   comm.barrier()
   if rank == 0:
      all_data = json.load(open(args.json_file))
      end_time = time.time()
      duration = end_time - start_time
      all_data['combined']['write_lhe_runtime'] = duration
      json.dump(all_data,open(args.json_file,'w'),indent=3,sort_keys=True)

if __name__ == '__main__':
   main()