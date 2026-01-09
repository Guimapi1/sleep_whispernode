"""
Real-time plot of Current vs Time from TC66C
Updates dynamically as new data arrives
"""

import serial
import argparse
import struct
import sys
from Crypto.Cipher import AES
from collections import namedtuple
from time import sleep, monotonic, strftime, localtime
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import numpy as np

# Import TC66C class
import sys
sys.path.insert(0, '/home/c24guima/Documents/PlatformIO/Projects/sleep_v1/tc66c')
from TC66C import TC66C

parser = argparse.ArgumentParser()
DEFPORT = '/dev/ttyACM0'

parser.add_argument('port', nargs='?', help='port (default =' + DEFPORT,
                    action='store', type=str, default=DEFPORT)
parser.add_argument('--time', '-t', help='interval time in seconds between polls (def=1.0)',
                    dest='int_time', action='store', type=float, default=1.0)


class RealtimePlotter:
    def __init__(self, tc66, update_interval=1000):
        """
        Initialize the real-time plotter
        
        Args:
            tc66: TC66C device instance
            update_interval: interval in ms for plot updates
        """
        self.tc66 = tc66
        self.update_interval = update_interval
        
        # Data buffers
        self.times = []
        self.currents = []
        self.start_time = monotonic()
        
        # Create figure and axis
        self.fig, self.ax = plt.subplots(figsize=(12, 6))
        self.line, = self.ax.plot([], [], 'b-', linewidth=2, label='Current')
        
        # Setup plot
        self.ax.set_xlabel('Time (s)', fontsize=12)
        self.ax.set_ylabel('Current (A)', fontsize=12)
        self.ax.set_title('TC66C Real-time Current Monitoring', fontsize=14, fontweight='bold')
        self.ax.grid(True, alpha=0.3)
        self.ax.legend(loc='upper left')
        
        # Setup animation
        self.ani = FuncAnimation(self.fig, self.update_plot, interval=update_interval,
                                blit=False, cache_frame_data=False)
        
    def update_plot(self, frame):
        """Update plot with new data"""
        try:
            # Poll new data
            pd = self.tc66.Poll()
            current_time = monotonic() - self.start_time
            
            # Add data
            self.times.append(current_time)
            self.currents.append(pd.Current)
            
            # Print to terminal
            print(f"Time: {current_time:6.1f}s | Current: {pd.Current:8.5f}A | Voltage: {pd.Volt:7.4f}V | Power: {pd.Power:8.4f}W")
            
            # Update line data
            self.line.set_data(self.times, self.currents)
            
            # Auto-scale axes
            if len(self.times) > 0:
                self.ax.set_xlim(max(0, current_time - 60), current_time + 5)
                if len(self.currents) > 0:
                    min_curr = min(self.currents)
                    max_curr = max(self.currents)
                    margin = (max_curr - min_curr) * 0.1 if max_curr != min_curr else 0.1
                    self.ax.set_ylim(min_curr - margin, max_curr + margin)
            
        except Exception as e:
            print(f"Error reading data: {e}")
        
        return self.line,
    
    def show(self):
        """Display the plot"""
        plt.tight_layout()
        plt.show()


if __name__ == "__main__":
    arg = parser.parse_args()
    
    try:
        print(f"Connecting to TC66C on {arg.port}...")
        tc66 = TC66C(arg.port)
        print("Connected successfully!")
        print("Starting real-time monitoring (press Ctrl+C to stop)...\n")
        
        # Create and show plotter
        plotter = RealtimePlotter(tc66, update_interval=int(arg.int_time * 1000))
        plotter.show()
        
    except KeyboardInterrupt:
        print("\n\nMonitoring stopped by user.")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
