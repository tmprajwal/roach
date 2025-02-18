#!/usr/bin/env python
'''
Online Digitizer and Analyzer for
Project8: Towards measuring the mass of neutrino.
Author:Prajwal Mohanmurthy
       prajwal@mohanmurthy.com
       LNS MIT
Adapted from Tutorial3 script (Jason Manley).
'''

import corr,time,numpy,struct,sys,logging,pylab,matplotlib

bitstream = 'proj81.bof'
katcp_port=7147

def exit_fail():
    print 'FAILURE DETECTED. Log entries:\n',lh.printMessages()
    try:
        fpga.stop()
    except: pass
    raise
    exit()

def exit_clean():
    try:
        fpga.stop()
    except: pass
    exit()

def get_data():
    #get the data...    
    acc_n = fpga.read_uint('acc_cnt')
    a_0=struct.unpack('>1024l',fpga.read('even',1024*4,0))
    a_1=struct.unpack('>1024l',fpga.read('odd',1024*4,0))

    interleave_a=[]

    for i in range(1024):
        interleave_a.append(a_0[i])
        interleave_a.append(a_1[i])
    return acc_n, interleave_a 

def plot_spectrum():
    matplotlib.pyplot.clf()
    acc_n, interleave_a = get_data()

    matplotlib.pylab.plot(interleave_a)
    #matplotlib.pylab.semilogy(interleave_a)
    matplotlib.pylab.title('Integration number %i.'%acc_n)
    matplotlib.pylab.ylabel('Power (arbitrary units)')
    matplotlib.pylab.ylim(0)
    matplotlib.pylab.grid()
    matplotlib.pylab.xlabel('Channel')
    matplotlib.pylab.xlim(0,2048)
    fig.canvas.draw()
    fig.canvas.manager.window.after(100, plot_spectrum)


#START OF MAIN:

if __name__ == '__main__':
    from optparse import OptionParser


    p = OptionParser()
    p.set_usage('spectrometer.py <ROACH_HOSTNAME_or_IP> [options]')
    p.set_description(__doc__)
    p.add_option('-l', '--acc_len', dest='acc_len', type='int',default=2*(2**28)/2048,
        help='Set the number of vectors to accumulate between dumps. default is 2*(2^28)/2048, or just under 2 seconds.')
    p.add_option('-g', '--gain', dest='gain', type='int',default=0xffffffff,
        help='Set the digital gain (6bit quantisation scalar). Default is 0xffffffff (max), good for wideband noise. Set lower for CW tones.')
    p.add_option('-s', '--skip', dest='skip', action='store_true',
        help='Skip reprogramming the FPGA and configuring EQ.')
    p.add_option('-b', '--bof', dest='boffile',type='str', default='',
        help='Specify the bof file to load')
    opts, args = p.parse_args(sys.argv[1:])

    if args==[]:
        print 'Please specify a ROACH board. Run with the -h flag to see all options.\nExiting.'
        exit()
    else:
        roach = args[0] 
    if opts.boffile != '':
        bitstream = opts.boffile

try:
    loggers = []
    lh=corr.log_handlers.DebugLogHandler()
    logger = logging.getLogger(roach)
    logger.addHandler(lh)
    logger.setLevel(10)

    print('Connecting to server %s on port %i... '%(roach,katcp_port)),
    fpga = corr.katcp_wrapper.FpgaClient(roach, katcp_port, timeout=10,logger=logger)
    time.sleep(1)

    if fpga.is_connected():
        print 'ok\n'
    else:
        print 'ERROR connecting to server %s on port %i.\n'%(roach,katcp_port)
        exit_fail()

    print '------------------------'
    print 'Programming FPGA with %s...' %bitstream,
    if not opts.skip:
        fpga.progdev(bitstream)
        print 'done'
    else:
        print 'Skipped.'

    print 'Configuring accumulation period...',
    fpga.write_int('acc_len',opts.acc_len)
    print 'done'

    print 'Resetting counters...',
    fpga.write_int('cnt_rst',1) 
    fpga.write_int('cnt_rst',0) 
    print 'done'

    print 'Setting digital gain of all channels to %i...'%opts.gain,
    if not opts.skip:
        fpga.write_int('gain',opts.gain) #write the same gain for all inputs, all channels
        print 'done'
    else:   
        print 'Skipped.'

    #set up the figure with a subplot to be plotted
    fig = matplotlib.pyplot.figure()
    ax = fig.add_subplot(1,1,1)

    # start the process
    fig.canvas.manager.window.after(100, plot_spectrum)
    matplotlib.pyplot.show()
    print 'Plot started.'

except KeyboardInterrupt:
    exit_clean()
except:
    exit_fail()

exit_clean()

