import pandas as pd
idx = pd.date_range('2024-01-02', periods=3, tz='UTC')
ser = pd.Series(range(3), index=idx)
target = pd.DatetimeIndex(['2024-01-02', '2024-01-03'])
print('target dtype', target.dtype)
try:
    out = ser.reindex(target)
    print(out)
except Exception as exc:
    import traceback
    traceback.print_exc()
