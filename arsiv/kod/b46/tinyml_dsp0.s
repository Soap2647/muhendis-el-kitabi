	.cpu cortex-m4
	.arch armv7e-m
	.fpu fpv4-sp-d16
	.eabi_attribute 27, 1
	.eabi_attribute 28, 1
	.eabi_attribute 20, 1
	.eabi_attribute 21, 1
	.eabi_attribute 23, 3
	.eabi_attribute 24, 1
	.eabi_attribute 25, 1
	.eabi_attribute 26, 1
	.eabi_attribute 30, 4
	.eabi_attribute 34, 1
	.eabi_attribute 18, 4
	.file	"tinyml.c"
	.text
	.section	.text.tm_ozellik,"ax",%progbits
	.align	1
	.global	tm_ozellik
	.syntax unified
	.thumb
	.thumb_func
	.type	tm_ozellik, %function
tm_ozellik:
	@ args = 0, pretend = 0, frame = 0
	@ frame_needed = 0, uses_anonymous_args = 0
	vldr.32	s8, .L12
	vldr.32	s7, .L12+4
	push	{r4, lr}
	vmov.f32	s6, #1.55e+1
	add	r4, r0, #16
.L6:
	vldr.32	s14, [r0]
	vldr.32	s15, .L12+8
	mov	r3, r0
	vmov.f32	s10, s14
	add	r2, r0, #512
.L4:
	mov	ip, r3
	vldr.32	s13, [ip]
	vcmp.f32	s13, s14
	vmrs	APSR_nzcv, FPSCR
	vcmp.f32	s13, s10
	add	r3, r3, #16
	it	mi
	vmovmi.f32	s14, s13
	vmrs	APSR_nzcv, FPSCR
	it	gt
	vmovgt.f32	s10, s13
	cmp	r2, r3
	vadd.f32	s15, s15, s13
	bne	.L4
	vldr.32	s11, .L12+8
	vmul.f32	s15, s15, s8
	mov	r2, r0
	movs	r3, #0
	vmov.f32	s13, s11
.L5:
	vmov	s9, r3	@ int
	mov	ip, r2
	vldr.32	s12, [ip]
	vcvt.f32.s32	s9, s9
	vsub.f32	s12, s12, s15
	vsub.f32	s9, s9, s6
	adds	r3, r3, #1
	cmp	r3, #32
	vmla.f32	s13, s12, s12
	add	r2, r2, #16
	vmla.f32	s11, s9, s12
	bne	.L5
	vmul.f32	s13, s13, s8
	vstmia.32	r1!, {s15}
	vsqrt.f32	s15, s13
	adds	r0, r0, #4
	cmp	r4, r0
	vstr.32	s14, [r1, #28]
	vstr.32	s15, [r1, #12]
	vdiv.f32	s15, s11, s7
	vstr.32	s10, [r1, #44]
	vstr.32	s15, [r1, #60]
	bne	.L6
	pop	{r4, pc}
.L13:
	.align	2
.L12:
	.word	1023410176
	.word	1160413184
	.word	0
	.size	tm_ozellik, .-tm_ozellik
	.section	.text.tm_girdi_kuantize,"ax",%progbits
	.align	1
	.global	tm_girdi_kuantize
	.syntax unified
	.thumb
	.thumb_func
	.type	tm_girdi_kuantize, %function
tm_girdi_kuantize:
	@ args = 0, pretend = 0, frame = 0
	@ frame_needed = 0, uses_anonymous_args = 0
	push	{r4, r5, r6, lr}
	ldr	r2, .L20
	ldr	r4, .L20+4
	vldr.32	s14, .L20+8
	subs	r1, r1, #1
	add	r5, r0, #80
	vmov.f32	s13, #5.0e-1
	mvn	r6, #127
.L17:
	vldmia.32	r0!, {s15}
	vldmia.32	r4!, {s12}
	vldmia.32	r2!, {s11}
	vsub.f32	s15, s15, s12
	vdiv.f32	s12, s15, s11
	vdiv.f32	s15, s12, s14
	vadd.f32	s15, s15, s13
	vcvt.s32.f32	s12, s15
	vmov	r3, s12	@ int
	vcvt.f32.s32	s12, s12
	vcmpe.f32	s12, s15
	vmrs	APSR_nzcv, FPSCR
	it	gt
	addgt	r3, r3, #-1
	adds	r3, r3, #7
	cmp	r3, #127
	it	ge
	movge	r3, #127
	cmp	r3, r6
	it	lt
	movlt	r3, r6
	cmp	r5, r0
	strb	r3, [r1, #1]!
	bne	.L17
	pop	{r4, r5, r6, pc}
.L21:
	.align	2
.L20:
	.word	TM_SD
	.word	TM_MU
	.word	1034412533
	.size	tm_girdi_kuantize, .-tm_girdi_kuantize
	.section	.text.tm_ileri,"ax",%progbits
	.align	1
	.global	tm_ileri
	.syntax unified
	.thumb
	.thumb_func
	.type	tm_ileri, %function
tm_ileri:
	@ args = 0, pretend = 0, frame = 24
	@ frame_needed = 0, uses_anonymous_args = 0
	push	{r4, r5, r6, r7, r8, r9, r10, fp, lr}
	sub	sp, sp, #28
	ldr	r3, .L32
	str	r3, [sp, #4]
	ldr	lr, .L32+20
	ldr	r7, .L32+4
	ldr	r2, .L32+8
	str	r0, [sp, #12]
	add	r3, sp, #16
	mov	fp, r1
	mov	ip, r3
	movs	r0, #0
	movs	r4, #1
.L25:
	ldr	r5, [sp, #12]
	ldr	r1, [lr], #4
	str	r1, [sp, #8]
	add	r8, r5, #-1
	subs	r6, r2, #1
	movs	r5, #0
	add	r9, r2, #19
.L23:
	ldrsb	r1, [r6, #1]!
	ldrsb	r10, [r8, #1]!
	cmp	r9, r6
	smlabb	r5, r1, r10, r5
	bne	.L23
	ldr	r6, [sp, #4]
	ldr	r1, [sp, #8]
	ldr	r8, [r6], #4
	str	r6, [sp, #4]
	sub	r10, r8, #33
	rsb	r6, r8, #33
	add	r1, r1, r5
	ldr	r9, [r7], #4
	add	r5, r8, #-1
	lsl	r10, r4, r10
	lsr	r6, r4, r6
	orr	r6, r10, r6
	lsl	r5, r4, r5
	smlal	r5, r6, r1, r9
	rsb	r9, r8, #32
	subs	r1, r8, #32
	lsr	r5, r5, r8
	lsl	r9, r6, r9
	it	pl
	asrpl	r1, r6, r1
	orr	r5, r5, r9
	it	pl
	orrpl	r5, r5, r1
	subs	r5, r5, #128
	cmp	r5, #127
	it	ge
	movge	r5, #127
	mvn	r1, #127
	cmp	r5, r1
	add	r0, r0, #1
	it	lt
	movlt	r5, r1
	cmp	r0, #8
	strb	r5, [ip], #1
	add	r2, r2, #20
	bne	.L25
	movs	r2, #0
	ldr	r4, .L32+12
	mov	r0, r3
	mov	r1, r2
.L26:
	ldrsb	r6, [r4], #1
	ldrsb	r5, [r0], #1
	adds	r1, r1, #1
	cmp	r1, #8
	mla	r2, r6, r5, r2
	bne	.L26
	add	r2, r2, #8320
	adds	r2, r2, #19
	movs	r1, #0
	ldr	r0, .L32+16
	str	r2, [fp]
	mov	r2, r1
.L27:
	ldrsb	r4, [r3], #1
	ldrsb	r5, [r0, #1]!
	adds	r1, r1, #1
	cmp	r1, #8
	smlabb	r2, r5, r4, r2
	bne	.L27
	add	r2, r2, #20352
	adds	r2, r2, #109
	str	r2, [fp, #4]
	add	sp, sp, #28
	@ sp needed
	pop	{r4, r5, r6, r7, r8, r9, r10, fp, pc}
.L33:
	.align	2
.L32:
	.word	TM_RS1
	.word	TM_M1
	.word	TM_W1
	.word	TM_W2
	.word	TM_W2+7
	.word	TM_B1
	.size	tm_ileri, .-tm_ileri
	.section	.text.tm_siniflandir,"ax",%progbits
	.align	1
	.global	tm_siniflandir
	.syntax unified
	.thumb
	.thumb_func
	.type	tm_siniflandir, %function
tm_siniflandir:
	@ args = 0, pretend = 0, frame = 112
	@ frame_needed = 0, uses_anonymous_args = 0
	push	{lr}
	sub	sp, sp, #116
	add	r1, sp, #32
	bl	tm_ozellik
	add	r1, sp, #12
	add	r0, sp, #32
	bl	tm_girdi_kuantize
	add	r0, sp, #12
	add	r1, sp, #4
	bl	tm_ileri
	ldrd	r3, r0, [sp, #4]
	cmp	r0, r3
	ite	le
	movle	r0, #0
	movgt	r0, #1
	add	sp, sp, #116
	@ sp needed
	ldr	pc, [sp], #4
	.size	tm_siniflandir, .-tm_siniflandir
	.section	.rodata.TM_W2,"a"
	.type	TM_W2, %object
	.size	TM_W2, 16
TM_W2:
	.ascii	"U)\205\177\377\021\267\374\303\377l\270T;8\357"
	.section	.rodata.TM_RS1,"a"
	.align	2
	.type	TM_RS1, %object
	.size	TM_RS1, 32
TM_RS1:
	.word	37
	.word	37
	.word	37
	.word	37
	.word	37
	.word	38
	.word	37
	.word	37
	.section	.rodata.TM_M1,"a"
	.align	2
	.type	TM_M1, %object
	.size	TM_M1, 32
TM_M1:
	.word	1362398346
	.word	1111630342
	.word	1950243921
	.word	1974131210
	.word	1375567070
	.word	1455104087
	.word	1921711117
	.word	1710252355
	.section	.rodata.TM_B1,"a"
	.align	2
	.type	TM_B1, %object
	.size	TM_B1, 32
TM_B1:
	.word	2112
	.word	12
	.word	1078
	.word	2232
	.word	-58
	.word	1283
	.word	-2525
	.word	579
	.section	.rodata.TM_W1,"a"
	.type	TM_W1, %object
	.size	TM_W1, 160
TM_W1:
	.ascii	"\372.\033+\240\255\232\201 \0167\367\340\274\325%(\275"
	.ascii	"\014S\022\260\001\020(\201\314\363\177F\275-\352\364"
	.ascii	"\331\357r\300.\037\004G\334\032I\272\177d\027\351\327"
	.ascii	"\357\322\327$,\266\303\371\326\032&2\030\257\260\266"
	.ascii	"\201\024\376%'\324\350\255\361>\256\001@\017\002\320"
	.ascii	"=\036\0359W\031\351\374\231+M\320!\351\353\345\201:"
	.ascii	"\342\030\177)\227t\376\377\250\352\322\244\262fp\253"
	.ascii	"\260\014\240\335\012\026\025\376H\024\362\005\343\346"
	.ascii	"\007\037!\375\365=\1779$\320\004\177\351\324\376\241"
	.ascii	"\003\006\347>\341\010\324\364 \3038\345\035"
	.section	.rodata.TM_SD,"a"
	.align	2
	.type	TM_SD, %object
	.size	TM_SD, 80
TM_SD:
	.word	1035361294
	.word	1083066119
	.word	1099701846
	.word	1089062899
	.word	1010378406
	.word	1061391357
	.word	1080459578
	.word	1061265478
	.word	1036162401
	.word	1082820781
	.word	1098710885
	.word	1089254819
	.word	1035066644
	.word	1084209638
	.word	1102845738
	.word	1088800657
	.word	984472353
	.word	1034567068
	.word	1040464252
	.word	1032449989
	.section	.rodata.TM_MU,"a"
	.align	2
	.type	TM_MU, %object
	.size	TM_MU, 80
TM_MU:
	.word	1080853863
	.word	1107509493
	.word	1112100606
	.word	1104674600
	.word	1004839646
	.word	1050282359
	.word	1083292004
	.word	1052888701
	.word	1080797815
	.word	1107388003
	.word	1110401717
	.word	1104392199
	.word	1080909879
	.word	1107665194
	.word	1114558125
	.word	1105074971
	.word	-1178615631
	.word	1021418858
	.word	-1150696364
	.word	-1132400426
	.ident	"GCC: (GNU Tools for STM32 13.3.rel1.20240926-1715) 13.3.1 20240614"
