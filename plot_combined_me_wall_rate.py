import glob
import argparse,logging
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
logger = logging.getLogger(__name__)





def main():
   ''' simple starter program that can be copied for use when starting a new script. '''
   logging_format = '%(asctime)s %(levelname)s:%(name)s:%(message)s'
   logging_datefmt = '%Y-%m-%d %H:%M:%S'
   logging_level = logging.INFO
   
   parser = argparse.ArgumentParser(description='')
   parser.add_argument('-g','--glob',help='glob string for input csv',required=True)

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
    
   filelist = glob.glob(args.glob)

   dfs = []
   for filename in filelist:
      print(filename)
      df = pd.read_csv(filename)
      if '1rpgpu' in filename:
         df['ranks_per_gpu'] = 1
      elif '2rpgpu' in filename:
         df['ranks_per_gpu'] = 2
      elif '8rpgpu' in filename:
         df['ranks_per_gpu'] = 8
      dfs.append(df)

   df = pd.concat(dfs,ignore_index=True)
   df['ratio'] = 0.
   df['r1val'] = 0.
   r1v = df[df['ranks_per_gpu'] == 1]['me_per_madeventtime_per_gpu']
   print(r1v)
   df.loc[ df['ranks_per_gpu'] == 1, 'r1val'] = r1v.values
   df.loc[ df['ranks_per_gpu'] == 2, 'r1val'] = r1v.values
   df.loc[ df['ranks_per_gpu'] == 8, 'r1val'] = r1v.values

   df['ratio'] = df['me_per_madeventtime_per_gpu'] / df['r1val']

   ax = sns.lineplot(df,x='nodes',y='ratio',hue='ranks_per_gpu',palette=['r','g','b'],marker='o')
   ax.set_xlabel('nodes')
   ax.set_ylabel('ME per wall-time per GPU (norm)')
   # ax.set_yscale('log')
   plt.savefig('combo_me_wall_rate.png',dpi=160,bbox_inches='tight')

   print(df)

if __name__ == '__main__':
   main()
