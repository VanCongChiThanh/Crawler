import numpy as np
import matplotlib.pyplot as plt

# Thông số
A = 2 # Biên độ xung
tau = 1  # Độ rộng xung
T0 = 4 * tau  # Chu kỳ (T0 = 2 * tau)
k_vals = np.arange(-5, 6)  # Giá trị k từ -5 đến 5

# Tần số cơ bản
F0 = 1 / T0

# Tính hệ số Fourier c_k
ck = (A * tau / T0) * np.sinc(k_vals * F0 * tau)

# Phổ Biên Độ
magnitude_spectrum = np.abs(ck)

# Chuyển đổi từ k sang f
frequencies = k_vals * F0

# Vẽ phổ biên độ theo tần số
plt.figure(figsize=(8, 5))
plt.stem(frequencies, magnitude_spectrum, basefmt=" ")
plt.title("Phổ Biên Độ theo Tần Số")
plt.xlabel("Tần số f (Hz)")
plt.ylabel("|c_k|")
plt.grid(True)
plt.xlim(-3, 3)  # Giới hạn trục x
plt.ylim(0, 1.2)  # Giới hạn trục y
plt.show()
