.section .text

 LA fp, 0x30000000
 LA sp, 0x30000008

 ADDI t0, zero, 0
 SW t0, 0(fp)
 SW t0, 4(fp)

read_n:
 LA t0, 0x10000000
 PUTS t0
 GETI t0
 SW t0, 0(fp)
 BLE t0, zero, read_n

collatz_loop:
 LW t0, 0(fp)
 ADDI t1, zero, 1
 BLE t0, t1, done

 PUTI t0

 ADDI t1, zero, 2
 DIV t2, t0, t1
 MUL t3, t2, t1
 SUB t4, t0, t3
 BEQ t4, zero, even_case

odd_case:
 ADDI t5, zero, 3
 MUL t6, t0, t5
 ADDI t6, t6, 1
 SW t6, 0(fp)

 LW t5, 4(fp)
 ADDI t5, t5, 1
 SW t5, 4(fp)
 J collatz_loop

even_case:
 SW t2, 0(fp)

 LW t5, 4(fp)
 ADDI t5, t5, 1
 SW t5, 4(fp)
 J collatz_loop

done:
 LW t0, 0(fp)
 PUTI t0
 LW t0, 4(fp)
 PUTI t0
 HALT

.section .strings
0x10000000 "Please enter a positive integer\n"