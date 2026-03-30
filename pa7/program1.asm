.section .text

 GETI t0
 LA t1, 0x20000000
 SW t0, 0(t1)

 GETI t0
 LA t1, 0x20000004
 SW t0, 0(t1)

 LA t1, 0x20000000
 LW t2, 0(t1)

 LA t1, 0x20000004
 LW t3, 0(t1)

 BLT t2, t3, less_than
 BEQ t2, t3, equal_to
 J greater_than

less_than:
 LA t0, 0x10000000
 PUTS t0
 HALT

equal_to:
 LA t0, 0x10000004
 PUTS t0
 HALT

greater_than:
 LA t0, 0x10000008
 PUTS t0
 HALT

.section .strings
0x10000000 "a is less than b\n"
0x10000004 "a is equal to b\n"
0x10000008 "a is greater than b\n"