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
   ''' MPI program to parse the MadEvent output and save it to a shared output file in json format '''
   logging_format = '%(asctime)s %(levelname)s:' + ('%05d' % rank) + ':%(name)s:%(message)s'
   logging_datefmt = '%Y-%m-%d %H:%M:%S'
   logging_level = logging.INFO
   
   parser = argparse.ArgumentParser(description='')
   parser.add_argument('-i','--input',help='name of local MadEvent STDOUT file.',required=True)
   parser.add_argument('-o','--output',help='output filename for the combined json file',required=True)
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
   
   # load existing file
   existing_data = json.load(open(args.output))
   
   logger.debug('opening file %s',args.input)
   # every rank should read their local file from RAM disk
   output_data = {'rank':rank,'nranks':nranks,'local_rank':local_rank,'local_nranks':local_nranks}
   with open(args.input,mode='r') as file_handle:
      # read lines in file
      # parse this line: "WARNING! Instantiate device Bridge (nevt=16384, gpublocks=64, gputhreads=256, gpublocks*gputhreads=16384)"
      for line in file_handle.readlines():
         logger.debug('line: %s',line)
         if line.startswith('WARNING! Instantiate device Bridge'):
            startindex = line.find('(')
            endindex = line.find(')',startindex)
            parts = line[startindex+1:endindex].split(',')
            for part in parts:
               left,right = part.split('=')
               output_data[left.strip()] = int(right)
         elif line.startswith(' [COUNTERS]'):
            if 'PROGRAM TOTAL' in line:
               parts = line.split(':')
               output_data['program_total_sec'] = float(parts[1].replace('s','').strip())
            elif 'EVENTLOOP TOTAL' in line:
               parts = line.split(':')
               output_data['eventloop_total_sec'] = float(parts[1].replace('s','').strip())
            elif 'Fortran Overhead' in line:
               parts = line.split(':')
               startidx = parts[0].find('(')
               endidx = parts[0].find(')',startidx)
               output_data['fortran_overhead_int'] = int(parts[0][startidx+1:endidx])
               output_data['fortran_overhead_sec'] = float(parts[1].replace('s','').strip())
            elif 'SYCL MEs' in line:
               partsA = line.split(':')
               startidx = partsA[0].find('(')
               endidx = partsA[0].find(')',startidx)
               output_data['sycl_mes_int'] = int(partsA[0][startidx+1:endidx])
               partsB = partsA[1].split('for')
               output_data['sycl_mes_sec'] = float(partsB[0].replace('s','').strip())
               partsC = partsB[1].split('events')
               output_data['sycl_total_events'] = int(partsC[0])
         elif line.strip().startswith('with seed'):
            parts = line.split()
            output_data['random_seed'] = int(parts[-1])
         elif line.strip().startswith('Ranmar initialization seeds'):
            parts = line[len(' Ranmar initialization seeds ')+1:].split()
            output_data['ranmar_seeds'] = (int(parts[0]),int(parts[1]))
         elif 'Found' in line and 'events' in line:
            parts = line.split()
            output_data['found_events'] = int(parts[1])
         elif 'Wrote' in line and 'events' in line:
            parts = line.split()
            output_data['wrote_events'] = int(parts[1])
         elif line.startswith('Actual xsec'):
            parts = line.split()
            output_data['xsec'] = float(parts[-1])
         elif line.startswith('real '):
            parts = line.split()
            output_data['time_madevent_exe_sec'] = float(parts[-1])

   sum_sycl_mes_sec = comm.allreduce(output_data['sycl_mes_sec'])
   sum2_sycl_mes_sec = comm.allreduce(output_data['sycl_mes_sec']*output_data['sycl_mes_sec'])
   sum_program_total_sec = comm.allreduce(output_data['program_total_sec'])
   sum2_program_total_sec = comm.allreduce(output_data['program_total_sec']*output_data['program_total_sec'])
   sum_time_madevent_exe_sec = comm.allreduce(output_data['time_madevent_exe_sec'])
   sum2_time_madevent_exe_sec = comm.allreduce(output_data['time_madevent_exe_sec']*output_data['time_madevent_exe_sec'])


   # convert data to json string
   output_json = json.dumps(output_data,indent=3,sort_keys=True)

   logger.debug('json output: %s',output_json)

   # add json mark up so that combined output is a list of dictionaries
   if rank == 0:
      combined_data = {
         'sum_sycl_mes_sec': sum_sycl_mes_sec,
         'sum2_sycl_mes_sec': sum2_sycl_mes_sec,
         'sum_program_total_sec': sum_program_total_sec,
         'sum2_program_total_sec': sum2_program_total_sec,
         'sum_time_madevent_exe_sec': sum_time_madevent_exe_sec,
         'sum2_time_madevent_exe_sec': sum2_time_madevent_exe_sec,
         'nranks': nranks,
         'sycl_total_events_per_rank': output_data['sycl_total_events'],
      }
      
      for key,value in existing_data['combined'].items():
         combined_data[key] = value
      combined_data_json = json.dumps(combined_data,indent=3,sort_keys=True)

      output_json = '{\n  "combined": ' + combined_data_json + ',\n  "ranks": [' + output_json + ',\n'
   elif rank == nranks - 1:
      output_json = output_json + '\n]\n}'
   else:
      output_json = output_json + ',\n'
   
   # convert to bytes object
   output_json = bytes(output_json,'utf-8')
   # get size of data
   output_size = len(output_json)

   # determine size of the output
   logger.debug('json bytes: %d',output_size)
   # every rank needs to know the size of everyone elses data
   # do an all gather to share our size information
   all_output_sizes = comm.allgather(output_size)
   logger.debug('sent size of bytes: %d',output_size)
   # now calculate the bytes offset in the file
   offset = calc_starting_point(all_output_sizes,rank)
   logger.debug('offset = %d',offset)

   # now we open a file for writing
   logger.debug('writing to file: %s',args.output)
   mpi_file_handle = MPI.File.Open(comm,args.output, MPI.MODE_WRONLY | MPI.MODE_CREATE)
   mpi_file_handle.Write_at_all(offset,output_json)
   mpi_file_handle.Close()

   comm.barrier()
   if rank == 0:
      all_data = json.load(open(args.output))
      end_time = time.time()
      duration = end_time - start_time
      all_data['combined']['parse_runtime'] = duration
      json.dump(all_data,open(args.output,'w'),indent=3,sort_keys=True)



if __name__ == '__main__':
   main()