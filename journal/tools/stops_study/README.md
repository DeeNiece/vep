# Stops and trailing study (4H)

Reads cached price bars (1m, 5m, 15m) and the 4H alerts in data/study_4h.json plus the EDGE EXH labels in
data/study_edge.json. For each trade it follows price for up to 5 days and tests stop width (1x to 3x the
indicator stop), breakeven and trailing rules. Output: data/study_stops.json (shown in the Study tab).

Run order: build.py (merge price bars), sim.py, sim2.py. The price files came from TradingView data pulls in a
working folder, not from this repo. After the Plus chart export, point build.py at the exported files and
re-run to refresh the numbers. Alerts that fire between 23:00 and 06:30 HK are left out (no new trades then).
