from datetime import datetime
import time

now=datetime.now()
y=now.year
m=now.month
d=now.day

opening_date=datetime(now.year,month=5,day=17)
countdown = opening_date-now
sec=countdown.seconds

for i in range(sec,0,-1):
    hour=i//3600
    minute=(i//60) %60
    second=i%60

    print(f"countdown in:{countdown.days} Days{hour} Hours{minute} Minutes{second} Seconds",end='/r', flush=True)
    time.sleep(1)


