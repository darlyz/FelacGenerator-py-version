\ 双曲线方程显示算法文件 wavefexp.sch（不重算单刚快速显式算法）：
\ 空间离散后矩阵形式为
\                        [M][A]+[C][V]+[S][U] = [F]
\ 其中 V=dU/dt，A=dV/dt。对加速度 A 进行时间向前差分，载荷项更新为新时间值
\                 [M]([Vˉ]-[V])+[C][V]*Δt+[S][U]*Δt = [Fˉ]*Δt
\ 其中 Vˉ 记为 V 的后一时刻值，即 Vˉ=V(t+Δt)，Fˉ 同理，Δt为时间步长。
\ 对速度 Vˉ 再次进行时间向后差分可得
\         [M]([Uˉ]-[U])-[M][V]*Δt+[C][V]*Δt*Δt+[S][U]*Δt*Δt = [Fˉ]*Δt*Δt
\ 移项并整理得
\         [M][Uˉ] = [M][U]+[M][V]*Δt+[C][V]*Δt*Δt-[S][U]*Δt*Δt+[Fˉ]*Δt*Δt
\ ---------------------------------------------------------------------------
DEFI
STIF s
MASS m
DAMP c
LOAD f
TYPE w
MDTY l
INIT 2

EQUATION
VECT u,v
\......... 读取解空间中的 u,v 作为上一时刻的位移和速度 ........../
READ(s,unod) u,v
MATRIX = [s]
\..............线性方程组左端项(集中矩阵)................/
L,M = [m]
\????????????????????????????????????????????????????????/
L,C = [c]
\????????????????????????????????????????????????????????/
TM = [m]
\...................线性方程组右端项...................../
FORC = [m*u]+[m*v]*dt-[s*u]*dt*dt-[c*v]*dt*dt+[f]*dt*dt

SOLUTION u1
VECT u,v,u1
$cc // 通过 v = (u1-u)/Δt 计算当前速度
[v] = ([u1]-[u])/dt
$cc // 存储求解的当时刻位移和速度 u1 v
WRITE(o,unod) u1,v

@M
 m = 10;

END