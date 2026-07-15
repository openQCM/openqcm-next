import numpy as np
import matplotlib.pyplot as plt

# Sample data:
data = np.random.rand(100, 2)  # Assuming you have a 100x2 data matrix as an example
frequency = data[:, 0]
gain = data[:, 1]

# Assume these are the arrays for peaks (as an example):
peaks = np.array([0.2, 0.5, 0.75])

# Plot the entire signal:
plt.plot(frequency, gain, '-o', label='Signal')

# Highlight the peaks on the plot:
for peak in peaks:
    # Find the gain value closest to the peak frequency
    y_val = gain[np.argmin(np.abs(frequency - peak))]
    plt.plot(peak, y_val, 'ro')  # Highlight the peak with a red dot

plt.xlabel('Frequency')
plt.ylabel('Gain')
plt.title('Signal with Peaks Highlighted')
plt.legend()
plt.grid(True)
plt.show()
