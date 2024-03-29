DEFI
STIF s
MASS m
DAMP c
LOAD f
TYPE w
MDTY l
INIT 2

COEF uu1

EQUATION
VECT u1,v1,u,du,uu1
\ ================================================================
\ =    READ语句从指针数组unod中读取数据                          =
\ =    u1: 上一时间步的位移结果                                  =
\ =    v1: 由上一迭代步与上一时间步的位移结果算出的速度          =
\ =    u:  上一迭代步的位移结果                                  =
\ =    du: 本迭代步与上一迭代步的位移结果差值                    =
\ =    uu1:本迭代步的位移结果与上一时间步的位移结果的差值        =
\ ================================================================
READ(s,unod) u1,v1,u,du,uu1
\ ---------------------------------------------------------------
\ ................ M*U,tt + C*U,t = LU + F
\ ---------------------------------------------------------------
\ ................ U,t = V
\ ................ M*V,t + C*V - LU = F
\ ---------------------------------------------------------------
\ (V(n+1)+V(n))/2 = (U(n+1)-U(n))/DT
\ M*V,t + C*V - L(U(n+1)+U(n))/2 = F
\ M*(V(n+1)-V(n)) + C*(V(n+1)+V(n))*DT/2 - L(U(n+1)+U(n))*DT/2 = F*DT
\ M*(V(n+1)+V(n)) - M*V(n)*2 + C*(V(n+1)+V(n))*DT/2 - L(U(n+1)+U(n))*DT/2
\ = F*DT
\ M*(U(n+1)-U(n))*2/DT - M*V(n)*2 + C*(U(n+1)-U(n)) - L(U(n+1)+U(n))*DT/2
\ = F*DT
\ M*U(n+1)*2/DT  + C*U(n+1) - LU(n+1)*DT/2
\ = F*DT + M*V(n)*2 + M*U(n)*2/DT + C*U(n) + LU(n)*DT/2
\ M*U(n+1)  + C*U(n+1)*DT/2 - LU(n+1)*DT*DT/4
\ = F*DT*DT/2 + M*V(n)*DT + M*U(n) + C*U(n)*DT/2 + LU(n)*DT*DT/4
\ ---------------------------------------------------------------
\ (M+C*DT/2+S*DT*DT/4)*U(n+1)
\ = F*DT*DT/2 + M*V(n)*DT + M*U(n) + C*U(n)*DT/2 - S*U(n)*DT*DT/4
\ ---------------------------------------------------------------
MATRIX = [s]*dt*dt/4+[c]*dt/2+[m]
FORC=[f]*dt*dt/2+[m*u1]+[m*v1]*dt+[c*u1]*dt/2-[s*u1]*dt*dt/4+[s*u]*dt*dt/2

SOLUTION v
VECT u,u1,v1,ue,du,uu1,v
\ ================================================================
\ =    READ语句从指针数组unod中读取数据                          =
\ =    u1: 上一时间步的位移结果                                  =
\ =    v1: 由上一迭代步与上一时间步的位移结果算出的速度          =
\ =    u:  上一迭代步的位移结果                                  =
\ =    du: 本迭代步与上一迭代步的位移结果差值                    =
\ =    uu1:本迭代步的位移结果与上一时间步的位移结果的差值        =
\ ================================================================
READ(s,unod) u1,v1,u,du,uu1
$CC // === ue: 当前步结果与上一迭代步的差值，即当前迭代步增量 ===
[ue]=[v]-[u]
$CC if (it==1 && itn==1) {            // 如果为第一时间步中的第一迭代步
$CC // === 将本迭代步与上一迭代步的位移结果差值置为0.0 ===
[du]=0.0
$CC }
$CC aa = 0.0;
$CC ab = 0.0;
$CC bb = 0.0;
%NOD
%DOF
 aa = aa+[ue]*[ue];
 ab = ab+[ue]*[du];
 bb = bb+[du]*[du];
%DOF
%NOD
#sum double aa ab bb
$CC err = aa;                         // err 为当前迭代步误差
$CC if (itn==1) cc = 1.0;             // 迭代第一步取松弛因子为 1
$CC if (itn>1) {                      // 下面每一迭代步都调整松弛因子
$CC rab = sqrt(aa)*sqrt(bb);          // 当前增量UE与上一增量DU模乘积
$CC if (ab>0.5*rab) cc = cc*2.0;      // 若UE与DU夹角小于60°，松弛因子增倍
$CC if (ab>0.8*rab) cc = cc*2.0;      // 若UE与DU夹角小于37°，松弛因子再次增倍
$CC if (ab<0.0) cc = cc*0.5;          // 若UE与DU夹角大于90°，松弛因子减半
$CC if (ab<-0.40*rab) cc = cc*0.5;    // 若UE与DU夹角大于114°，松弛因子再次减半
$CC if (ab<-0.80*rab) cc = cc*0.5;    // 若UE与DU夹角大于143°，松弛因子再次减半
$CC }                                 //
$CC if (cc>1.0) cc = 1.0;             // 控制松弛因子不能大于1
$CC ul = 0.0;
%NOD
%DOF
$CC // === 根据松弛因子(cc)更新迭代步增量 ===
 [ue] = [ue]*cc;
$CC // === 计算本迭代步松弛后的结果v ===
 [v] = [u]+[ue];
$CC // === 计算本迭代步松弛后结果u的模平方的和ul ===
 ul = ul + [u]*[u];
%DOF
%NOD
#sum double ul
\$CC WRITE(*,*) 'it,itn,CC,ERR =',it,itn,CC,ERR
\$CC WRITE(*,*) 'AB,RAB =',AB,RAB
$CC // === 由上一时间步的位移结果与本迭代步的位移结果计算出速度结果v1 ===
[v1]=[v]/dt-[u1]/dt
$CC // === 将本迭代步位移结果v赋给u ===
[u]=[v]
$CC // === 计算本迭代步的位移结果与上一时间步的位移结果的差值 ===
[uu1]=[u]-[u1]
$CC // ===================================================================
$CC // =    收敛判断                                                     =
$CC // =    err足够小，或者err相对于计算结果的模的平方的和足够小         =
$CC // =    或者迭代步数超出最大迭代步，都会被判断为收敛，停止迭代       =
$CC // =    end为迭代收敛标志变量。                                      =
$CC // ===================================================================
$CC if (err<tolerance || err<tolerance*ul || itn>itnmax) end = 1;
#min int end
$CC if (end==1){                      // 如果收敛
$CC // === 更新位移计算结果 ===
[u1]=[v]                              
$CC itn=1;                            // 迭代步置1
$CC // === 本迭代步与上一迭代步的位移结果差值归0 ===
[du] = 0.0
$CC } else {                          // 若不收敛
$CC // === 更新本迭代步与上一迭代步的位移结果差值 ===
[du] = [ue]
$CC itn=itn+1;                        // 更新迭代步
$CC }
$CC // === 将本迭代步最终结果存储到指针数组unod中 === 
WRITE(o,unod) u1,v1,u,du,uu1

@SUBET
 double aa,bb,ab,rab,err,ul;
 static double cc;

END
