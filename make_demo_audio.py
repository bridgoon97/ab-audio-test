#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""生成演示用 A/B 音频对，输出到 demo_audio/ 文件夹。

包含 3 对样本（A 为原始版本，B 为处理版本），可直接用 ab_test.py 体验。
"""
import os

import numpy as np
import soundfile as sf

SR = 44100
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'demo_audio')


def normalize(x, peak=0.85):
    m = float(np.max(np.abs(x)))
    return x / m * peak if m > 0 else x


def fade(x, sr=SR, ms=8):
    n = int(sr * ms / 1000)
    if n * 2 >= len(x):
        return x
    env = np.ones(len(x))
    env[:n] = np.linspace(0, 1, n)
    env[-n:] = np.linspace(1, 0, n)
    return x * env


def save(name, x):
    sf.write(os.path.join(OUT, name), fade(normalize(x)).astype(np.float32), SR)
    print('已生成', name)


def lowpass_fft(x, sr, cutoff):
    X = np.fft.rfft(x)
    f = np.fft.rfftfreq(len(x), 1 / sr)
    X[f > cutoff] = 0
    return np.fft.irfft(X, n=len(x))


def pink_noise(n, sr, rng):
    X = np.fft.rfft(rng.standard_normal(n))
    f = np.fft.rfftfreq(n, 1 / sr)
    X[1:] = X[1:] / np.sqrt(f[1:])
    return np.fft.irfft(X, n)


def main():
    os.makedirs(OUT, exist_ok=True)
    rng = np.random.default_rng(7)

    # 1) 和弦：B 版本低通 1.5 kHz，高频泛音减少，听起来更"闷"
    t = np.arange(int(SR * 3)) / SR
    freqs = [220, 277.18, 329.63, 440, 554.37, 659.25]
    chord = sum(np.sin(2 * np.pi * f * t) * (0.8 ** i) * np.exp(-t * 1.2)
                for i, f in enumerate(freqs))
    save('chord_A.wav', chord)
    save('chord_B.wav', lowpass_fft(chord, SR, 1500))

    # 2) 粉红噪声：B 版本音量低 6 dB
    pink = pink_noise(SR * 3, SR, rng)
    save('pink_A.wav', pink)
    save('pink_B.wav', pink * 0.5)

    # 3) 扫频 100 Hz -> 8 kHz：B 版本做 4-bit 量化，模拟低码率失真
    dur = 4.0
    tt = np.arange(int(SR * dur)) / SR
    phase = 2 * np.pi * (100 * tt + (8000 - 100) * tt ** 2 / (2 * dur))
    sweep = np.sin(phase)
    save('sweep_A.wav', sweep)
    save('sweep_B.wav', np.round(sweep * 15) / 15)

    print(f'\n完成！共 3 对样本，保存在：{OUT}')
    print('运行 python ab_test.py，选择 demo_audio 文件夹即可开始体验。')


if __name__ == '__main__':
    main()
