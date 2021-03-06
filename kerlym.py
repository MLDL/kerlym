#!/usr/bin/env python
import os,random
#os.environ["THEANO_FLAGS"] = "mode=FAST_RUN,device=gpu%d,floatX=float32"%(random.randint(0,3))
import tempfile,logging,sys

from optparse import OptionParser
parser = OptionParser()
parser.add_option("-e", "--env", dest="env", default="MountainCar-v0",                  help="Which GYM Environment to run [%default]")
parser.add_option("-n", "--net", dest="net", default="simple_dnn",                      help="Which NN Architecture to use for Q-Function approximation [%default]")
parser.add_option("-f", "--update_freq", dest="update_freq", default=1000, type='int',  help='Frequency of NN updates specified in time steps [%default]')
parser.add_option("-u", "--update_size", dest="update_size", default=1100, type='int',  help='Number of samples to train on each update [%default]')
parser.add_option("-b", "--batch_size", dest="bs", default=32, type='int',              help="Batch size durring NN training [%default]")
parser.add_option("-o", "--dropout", dest="dropout", default=0.5, type='float',         help="Dropout rate in Q-Fn NN [%default]")
parser.add_option("-p", "--epsilon", dest="epsilon", default=0.1, type='float',         help="Exploration(1.0) vs Exploitation(0.0) action probability [%default]")
parser.add_option("-D", "--epsilon_decay", dest="epsilon_decay", default=1e-4, type='float',    help="Rate of epsilon decay: epsilon*=(1-decay) [%default]")
parser.add_option("-s", "--epsilon_min", dest="epsilon_min", default=0.05, type='float',help="Min epsilon value after decay [%default]")
parser.add_option("-d", "--discount", dest="discount", default=0.99, type='float',      help="Discount rate for future reards [%default]")
parser.add_option("-t", "--num_frames", dest="nframes", default=2, type='int',          help="Number of Sequential observations/timesteps to store in a single example [%default]")
parser.add_option("-m", "--max_mem", dest="maxmem", default=100000, type='int',         help="Max number of samples to remember [%default]")
parser.add_option("-P", "--plots", dest="plots", action="store_true", default=False,    help="Plot learning statistics while running [%default]")
parser.add_option("-F", "--plot_rate", dest="plot_rate", default=10, type='int',        help="Plot update rate in episodes [%default]")
parser.add_option("-S", "--submit", dest="submit", action="store_true", default=False,  help="Submit Results to OpenAI [%default]")
parser.add_option("-a", "--agent", dest="agent", default="ddqn",                        help="Which learning algorithm to use [%default]")
parser.add_option("-i", "--difference", dest="difference_obs", action="store_true", default=False,  help="Compute Difference Image for Training [%default]")
(options, args) = parser.parse_args()

print options.agent

training_dir = tempfile.mkdtemp()
logging.getLogger().setLevel(logging.DEBUG)

from gym import envs
env = envs.make(options.env)
if options.submit:
    env.monitor.start(training_dir)

import dqn
agent_constructor = {
    "dqn":dqn.DQN,
    "ddqn":dqn.D2QN
}[options.agent]

agent = agent_constructor(env, nframes=options.nframes, epsilon=options.epsilon, discount=options.discount, modelfactory=eval("dqn.%s"%(options.net)),
                    epsilon_schedule=lambda episode,epsilon: max(0.05, epsilon*(1-options.epsilon_decay)),
                    update_nsamp=options.update_size, batch_size=options.bs, dropout=options.dropout,
                    timesteps_per_batch=options.update_freq, stats_rate=options.plot_rate,
                    enable_plots = options.plots, max_memory = options.maxmem,
                    difference_obs = options.difference_obs )
agent.learn()
if options.submit:
    env.monitor.close()
    gym.upload(training_dir, algorithm_id="kerlym_%s_osh"%(options.agent))
