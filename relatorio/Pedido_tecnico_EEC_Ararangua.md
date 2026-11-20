# Minuta: pedido técnico ao fabricante (EEC) — radar de Araranguá

Minuta para a Defesa Civil de SC enviar à EEC, ou ao representante no Brasil, pelo canal do contrato de manutenção. O texto vai em inglês para o fabricante. Os anexos sugeridos são o resumo em PDF e 2 ou 3 volumes ODIM com chuva, de 18 a 20/11/2026.

---

**Subject:** Ranger X-band radar, Araranguá (SC, Brazil) — performance issues and configuration review

Dear EEC Support Team,

The Civil Defense of Santa Catarina operates the EEC Ranger dual-polarization X-band radar installed at Morro dos Conventos, Araranguá (−28.934548, −49.362490). EDGE 6.2.3 writes the data as ODIM_H5 PVOL. Our analysis of volumes from 16–20 November 2026 shows the following issues. We would appreciate your review and recommended corrective actions.

1. **Sensitivity.** The minimum detectable reflectivity at 0 dB SNR (TH − SNR) is about 30 dBZ at 20 km, 38 dBZ at 40 km and 44 dBZ at 60 km, which is about 41 dBZ at 50 km. The Ranger-X1 prototype specification (100 W, 67 µs LFM pulse) is 18 dBZ at 50 km. Our unit has a 410 W nominal transmitter, so its expected sensitivity should be similar or better. The observed deficit is about 22–29 dB. In moderate rain (35–45 dBZ) the SNR stays at 5–8 dB, which also degrades RhoHV, ZDR and PhiDP. Please verify:
   - the transmitted peak power at the antenna port, for both H and V;
   - whether pulse compression is enabled, and the configured waveform: pulse width, bandwidth and window;
   - losses in the waveguide, rotary joint and radome;
   - the receiver noise level and noise figure;
   - the radar constant and Z calibration.
2. **Blind zone.** All rays are saturated at about 74 dBZ up to 2.17 km (about 14.3 µs two-way). Is the short fill pulse (TFM waveform) enabled? If not, can it be enabled?
3. **PRF and Doppler.** The current dual-PRF is 400/267 Hz. At X band this gives a Nyquist velocity of 3.2 and 2.1 m/s (6.4 m/s extended). Velocity is effectively random (SQI 0.1–0.3), and the Doppler clutter filter removes a median of 44% of the rain rays at 0.5°. Since the processed range is 120 km, we request a change to **1200/900 Hz (4:3)**, which gives an extended Nyquist of about 29 m/s and an unambiguous range of 125 km, within the specified 200–2400 Hz range. Please confirm that the duty cycle and waveform are compatible, and enable second-trip suppression if available.
4. **ZDR calibration.** The median ZDR in rain is −0.3 to −1.3 dB. We request a vertical-pointing (birdbath) calibration and the procedure to repeat it periodically.
5. **Azimuth alignment.** Fixed clutter features suggest a possible azimuth offset of 2–4°. We request a sun-scan check.
6. **Site metadata.** The ODIM `where` group reports −28.9346, −49.3627 and 46 m. The surveyed antenna position is −28.934548, −49.362490, with the antenna at about 71 m above sea level (terrain about 68 m). Please correct the site configuration.
7. **Data delivery.** In 8 hours on 20 November 2026 there were 7 gaps longer than 15 minutes in the volumes delivered to our FTP, about 37% of the time. Please check whether the gaps originate in the radar, in the EDGE export, or in the transfer.

Please send us the factory sensitivity specification for this unit and the results of the checks above.

Best regards,
[nome, cargo — Defesa Civil de Santa Catarina]
