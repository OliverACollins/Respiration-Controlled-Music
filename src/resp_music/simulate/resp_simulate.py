import neurokit2 as nk
import pandas as pd
import matplotlib.pyplot as plt

rsp = nk.rsp_simulate(duration=600, method="sinusoidal", respiratory_rate=15)  # 10-minute duration, with 15 breaths/minute

signals, info = nk.rsp_process(rsp, sampling_rate=1000, report="text")

rsp_df = pd.DataFrame({"RSP_Simple": rsp})

rsp_df.to_csv("prerecorded_bridges\\data\\resp_simulate_15.csv", index = False)
print("Saved as resp_simulate_15.csv")

# ---- Plot ----
plt.figure(figsize=(10, 6))
plt.plot(rsp_df["RSP_Simple"])
plt.xlabel("Time (Samples)")
plt.ylabel("Amplitude")
plt.title("Simulated RESP Signal (Resp. Rate of 15)")
plt.tight_layout()
plt.show()