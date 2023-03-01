import numpy as np
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import os,sys,glob,json
import argparse,logging
from scipy import stats
logger = logging.getLogger(__name__)


def parse_bash_total_runtime(filename):
   with open(filename) as fh:
      for line in fh.readlines():
         if 'Completed Everything' in line:
            start_idx = line.find('[')
            end_idx = line.find(']',start_idx)
            seconds = int(line[start_idx+1:end_idx])
            return seconds
   
   raise Exception('failed to get total runtime from file: %s' % filename)


def parse_bash_runtime(filename):
   output_data = {}
   with open(filename) as fh:
      for line in fh.readlines():
         if 'run move_files' in line:
            start_idx = line.find('[')
            end_idx = line.find(']',start_idx)
            seconds = int(line[start_idx+1:end_idx])
            output_data['move_files_start'] = seconds
         elif 'run madevent' in line:
            start_idx = line.find('[')
            end_idx = line.find(']',start_idx)
            seconds = int(line[start_idx+1:end_idx])
            output_data['madevent_start'] = seconds
         elif 'run parse_madevent_output' in line:
            start_idx = line.find('[')
            end_idx = line.find(']',start_idx)
            seconds = int(line[start_idx+1:end_idx])
            output_data['parse_madevent_output_start'] = seconds
         elif 'run write_lhe' in line:
            start_idx = line.find('[')
            end_idx = line.find(']',start_idx)
            seconds = int(line[start_idx+1:end_idx])
            output_data['write_lhe_start'] = seconds
         elif 'done' in line:
            start_idx = line.find('[')
            end_idx = line.find(']',start_idx)
            seconds = int(line[start_idx+1:end_idx])
            output_data['write_lhe_end'] = seconds

   
   return output_data

def main():
   ''' simple starter program that can be copied for use when starting a new script. '''
   logging_format = '%(asctime)s %(levelname)s:%(name)s:%(message)s'
   logging_datefmt = '%Y-%m-%d %H:%M:%S'
   logging_level = logging.INFO
   
   parser = argparse.ArgumentParser(description='')
   parser.add_argument('-j','--jobid',help='name of jobid to process.',required=True,action='append')
   # parser.add_argument('-o','--output',help='output filename',required=True)
   parser.add_argument('-i','--input-base',help='input base path where to find job folders',required=True)
   parser.add_argument('-n','--gpus-per-node',help='number of gpus (or ranks) per node',type=int,required=True)
   parser.add_argument('-r','--ranks-per-gpu',help='number of ranks per gpu',type=int,required=True)
   parser.add_argument('-m','--machine',help='name of the machine',required=True)
   parser.add_argument('-t','--total-nodes',help='total number of nodes on machine',type=int,required=True)

   parser.add_argument('--debug', dest='debug', default=False, action='store_true', help="Set Logger to DEBUG")
   parser.add_argument('--error', dest='error', default=False, action='store_true', help="Set Logger to ERROR")
   parser.add_argument('--warning', dest='warning', default=False, action='store_true', help="Set Logger to ERROR")
   parser.add_argument('--logfilename',dest='logfilename',default=None,help='if set, logging information will go to file')
   args = parser.parse_args()

   ranks_per_node = args.gpus_per_node * args.ranks_per_gpu

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
   

   datalist = []
   for jobid in args.jobid:

      # get full run time from bash printout
      glob_str = os.path.join(args.input_base,jobid) + '*.OU'
      filelist = glob.glob(glob_str)
      total_runtime = parse_bash_total_runtime(filelist[0])

      # get bash run times
      glob_str = os.path.join(args.input_base,jobid) + '*/run_stdout.txt'
      filelist = glob.glob(glob_str)
      bash_runtime_data = parse_bash_runtime(filelist[0])

      # get combined stats
      glob_str = os.path.join(args.input_base,jobid) + '*/combined_stats.json'
      filelist = glob.glob(glob_str)
      jobdata = json.load(open(filelist[0]))
      jobdata['combined']['total_runtime_sec'] = total_runtime
      for key,value in bash_runtime_data.items():
         jobdata['combined'][key] = value
      datalist.append(jobdata['combined'])
   
   df = pd.DataFrame(datalist)

   df['sycl_mes_sec_mean'] = df['sum_sycl_mes_sec']/df['nranks']
   df['sycl_mes_sec_sigma'] = np.sqrt(df['sum2_sycl_mes_sec']/df['nranks'] - df['sycl_mes_sec_mean']*df['sycl_mes_sec_mean'])

   df['nodes'] = df['nranks'] / ranks_per_node

   df['program_total_sec_mean'] = df['sum_program_total_sec']/df['nranks']
   df['program_total_sec_sigma'] = np.sqrt(df['sum2_program_total_sec']/df['nranks'] - df['program_total_sec_mean']*df['program_total_sec_mean'])

   df['time_madevent_exe_sec_mean'] = df['sum_time_madevent_exe_sec']/df['nranks']
   df['time_madevent_exe_sec_sigma'] = np.sqrt(df['sum2_time_madevent_exe_sec']/df['nranks'] - df['time_madevent_exe_sec_mean']*df['time_madevent_exe_sec_mean'])

   df['event_rate_mean'] =  df['sycl_total_events_per_rank'] / df['sycl_mes_sec_mean']
   df['event_rate_sigma'] = np.sqrt( df['sycl_mes_sec_sigma'] ** 2 * (df['sycl_total_events_per_rank'] / (df['sycl_mes_sec_mean'] ** 2) ) ** 2 )

   df['events_total'] = df['sycl_total_events_per_rank'] * df['nranks']
   
   
   # Plot the Events per second per rank 
   ax = df.plot(x='nodes',y='event_rate_mean',legend=False,style='o-')
   plt.fill_between(df['nodes'],df['event_rate_mean'] - df['event_rate_sigma'],df['event_rate_mean'] + df['event_rate_sigma'],alpha=0.5)
   ax.set_xlabel('total %s nodes (%d max)' % (args.machine,args.total_nodes))
   ax.set_ylabel('ME/sec/rank')
   ax.set_yscale('log')
   plt.savefig('event_rate.png')
   
   # Plot total event calculated
   ax = df.plot(x='nodes',y='events_total',legend=False,style='o-')
   ax.set_xlabel('total %s nodes (%d max)' % (args.machine,args.total_nodes))
   ax.set_ylabel('total events')
   slope, intercept, r_value, p_value, std_err = stats.linregress(df['nodes'],df['events_total'])
   xlims = ax.get_xlim()
   x_vals = np.array(xlims)
   y_vals = intercept + slope * x_vals
   ax.plot(x_vals,y_vals)
   ax.text(xlims[0]+(xlims[1] - xlims[0])*0.1,ax.get_ylim()[1]*0.8,f'{slope:5.3g} * x + {intercept:5.3g}')
   plt.savefig('events_total.png')
   

   # Plot total run time
   ax = df.plot(x='nodes',y='total_runtime_sec',legend=False,style='o-')
   ax.set_xlabel('total %s nodes (%d max)' % (args.machine,args.total_nodes))
   ax.set_ylabel('total end-to-end runtime (sec)')
   plt.savefig('total_runtime.png')


   # Plot fraction of time spent in each section
   df['init_frac'] = df['move_files_start'] / df['total_runtime_sec']
   df['movefiles_frac'] = ( df['madevent_start'] - df['move_files_start'] ) / df['total_runtime_sec']
   df['madevent_frac'] = ( df['parse_madevent_output_start'] - df['madevent_start'] ) / df['total_runtime_sec']
   df['parse_frac'] = ( df['write_lhe_start'] - df['parse_madevent_output_start'] ) / df['total_runtime_sec']
   df['writelhe_frac'] = ( df['write_lhe_end'] - df['write_lhe_start'] ) / df['total_runtime_sec']
   df['final_frac'] = (df['total_runtime_sec'] - df['write_lhe_end']) / df['total_runtime_sec']

   # Plot fraction of time spent in each section for MadEvent
   df['fortran_overhead_frac'] = (df['program_total_sec_mean'] - df['sycl_mes_sec_mean']) / df['total_runtime_sec']
   df['sycl_mes_sec_frac'] = df['sycl_mes_sec_mean'] / df['total_runtime_sec']
   df['me_unknown'] = df['madevent_frac'] - df['fortran_overhead_frac'] - df['sycl_mes_sec_frac']
   

   # ax = df.plot(x='nodes',y='init_frac',        kind='bar',stacked=True,color='teal',         label='init')
   # df.plot(x='nodes',y='movefiles_frac',        kind='bar',stacked=True,color='orange', ax=ax,label='move')
   # df.plot(x='nodes',y='fortran_overhead_frac', kind='bar',stacked=True,color='red',    ax=ax,label='ME-Fortran')
   # df.plot(x='nodes',y='sycl_mes_sec_frac',     kind='bar',stacked=True,color='blue',   ax=ax,label='ME-Sycl')
   # df.plot(x='nodes',y='parse_frac',            kind='bar',stacked=True,color='green',  ax=ax,label='parse')
   # df.plot(x='nodes',y='writelhe_frac',         kind='bar',stacked=True,color='yellow', ax=ax,label='write-lhe')
   # df.plot(x='nodes',y='final_frac',            kind='bar',stacked=True,color='violet', ax=ax,label='final')
   # ax.set_ylim(0,1)
   # ax.legend()
   # plt.savefig('runtime_split.png')

   xdf = df[['init_frac','movefiles_frac','parse_frac','writelhe_frac','final_frac','fortran_overhead_frac','sycl_mes_sec_frac','me_unknown','nodes']]
   colors={'init_frac':'darkred','movefiles_frac':'red','parse_frac':'green','writelhe_frac':'blue','final_frac':'violet','fortran_overhead_frac':'orange','sycl_mes_sec_frac':'yellow','me_unknown':'black'}
   labels = ['init','move','parse','writelhe','final','me_fortran','me_sycl','unkonwn']
   ax = xdf.plot.bar(x='nodes',stacked=True,color=colors)
   ax.set_ylim(0,1)
   ax.set_xlabel('total %s nodes (%d max)' % (args.machine,args.total_nodes))
   ax.set_ylabel('fraction of total runtime')
   ax.grid(True,which='major',axis='y')
   lgd = ax.legend(bbox_to_anchor=(1.0, 1.05),labels=labels)
   txt = plt.gcf().text(0.92,0.4,'%d Ranks per GPU\n%d GPUs per node' % (args.ranks_per_gpu,args.gpus_per_node))
   plt.savefig('runtime_split.png',bbox_extra_artists=[lgd,txt],bbox_inches='tight')
   
   print(df[['init_frac','movefiles_frac','parse_frac','writelhe_frac','final_frac','fortran_overhead_frac','sycl_mes_sec_frac']])
   
if __name__ == '__main__':
   main()
