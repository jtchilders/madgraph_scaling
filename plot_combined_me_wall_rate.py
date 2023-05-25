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
   print('found %d files' % len(filelist))
   dfs = []
   for filename in filelist:
      print(filename)
      df = pd.read_csv(filename)
      df['ranks_per_gpu'] = 0
      df['machine'] = ''
      if '1rpgpu' in filename:
         df['ranks_per_gpu'] = 1
      elif '2rpgpu' in filename:
         df['ranks_per_gpu'] = 2
      elif '8rpgpu' in filename:
         df['ranks_per_gpu'] = 8

      if 'sunspot' in filename:
         df['machine'] = 'sunspot'
      elif 'polaris' in filename:
         df['machine'] = 'polaris'

      dfs.append(df)
   def func(x):
      try:
         y = df[(df['ranks_per_gpu'] == 1) * (df['machine'].str.contains('sunspot')) * (df['nodes'] == x['nodes'])]['me_per_madeventtime_per_gpu'].values[0]
         # print(y)
         return y
      except:
         logger.exception(x)
         raise
   df = pd.concat(dfs,ignore_index=True)
   df['ratio'] = 0.
   df['r1val'] =  df.apply(lambda x: func(x),axis=1)
   # print(df)

   df['ratio'] = df['me_per_madeventtime_per_gpu'] / df['r1val']
   
   fig, ax = plt.subplots()
   df[df['machine'].str.contains('sunspot')].groupby("ranks_per_gpu").plot(x="nodes", y="ratio", marker="o", ax=ax)
   df[df['machine'].str.contains('polaris')].groupby("ranks_per_gpu").plot(x='nodes', y='ratio', marker='x', ax = ax)
   handles, labels = ax.get_legend_handles_labels()
   labels = ["1 (Sunspot)","2 (Sunspot)","8 (Sunspot)","1 (Polaris)","2 (Polaris)"]
   labels  = [labels[0],labels[3],labels[1],labels[4],labels[2]]
   handles = [handles[0],handles[3],handles[1],handles[4],handles[2]]
   # reverse the order
   ax.legend(handles[::-1], labels[::-1],title='Ranks Per GPU')
   # ax = sns.lineplot(df,x='nodes',y='ratio',hue='ranks_per_gpu',palette=['r','g','b'],marker='o')
   ax.set_xlabel('Nodes (Sunspot: 6 GPUs/node, Polaris: 4 GPUs/node)')
   
   plt.title(r'$gg \rightarrow t\bar{t} gg$')
   ax.set_ylabel('ME per wall-time per GPU (norm)')
   # ax.set_yscale('log')
   plt.savefig('combo_me_wall_rate.png',dpi=160,bbox_inches='tight')

   print(df)

if __name__ == '__main__':
   main()
