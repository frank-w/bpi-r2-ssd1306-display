#!/bin/bash
chk_conf() {
	#echo "chk config..."
	ip link sh ppp9 | grep ,UP, >/dev/null;u=$?
	ping -c 1 192.168.0.8 >/dev/null;p=$?
	ip rule show | grep voip >/dev/null;ru=$?
	ip route show | grep ppp9 >/dev/null;ro=$?

	res=$(($u + $p<<8 + $ru<<16 + $ro<<24)) #shifting each result 8bits (return value can be 255 max)
	echo "config:$res";
	return $res
}

chk_traffic() {
	#echo "chk_traffic..."
	voip1_min=35
	voip2_min=20
	#calculate difference (actually i have 40 packets on voip1 and 20packets on voip2, don't know why it is the half...)
	str=$(tail -2 /var/log/voip1.log);ar=($str);res1=$(( ${ar[1]} - ${ar[0]} ));
	str=$(tail -2 /var/log/voip2.log);ar=($str);res2=$(( ${ar[1]} - ${ar[0]} ));

	if [[ $res1 -ge $voip1_min ]] && [[ $res2 -ge $voip2_min ]];
	then
		echo "traffic ok";
		return 0
	else
		echo "traffic:"$res1"/"$res2
		return 1
	fi
}

chk_conf
cc=$?
chk_traffic
ct=$?
if [[ $cc -eq 0 ]] && [[ $ct -eq 0 ]];then
	exit 0
fi
exit 1
