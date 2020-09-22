import numpy as np

DEG2RAD = np.pi/180.0

arms =   5
rad  =  40.0
a    = 270.0

for i in range(arms):
	print ('0.0 0.0')
	x = np.cos(a*DEG2RAD)*(rad+5.0)
	y = np.sin(a*DEG2RAD)*(rad+5.0)
	print('%.2f %.2f' % (x,y))
	a = (a+360.0/arms)%360.0

