import random
COMMANDS=['ip2long','long2ip','ip2BinHex','parseCIDR','isValidIP','isValidCIDR','toIPv6Format','toIPv6Expand','geoLocation']
def corpus():
    rng=random.Random(6734)
    ips=['',' ','\ufeff','0.0.0.0','255.255.255.255','192.168.0.1','001.002.003.004','01.2.3.4','0000.0.0.1','256.0.0.1','1.2.3.4\n','1.2.3.4\r\n','::','::1','2001:db8::1','FFFF:FFFF:FFFF:FFFF:FFFF:FFFF:FFFF:FFFF','1:0:0:2:0:0:3:4','::ffff:192.168.001.001',' ::1','::1 ','fe80::1%eth0','::%x','1:2:3:4:5:6:7:8%foo','1:2:3:4:5:6:192.168.0.1','1:2:3:4:5:6:7',':::','not-an-ip']
    ips += ['::1%a:0x10','::1%a:+f','::1%a:-f','::1%a:fffffffffffffffffff','::%a:b:c:d:e:f:g:h:i:j','::1%😀','fe80::1%zone:1:2:3','::1%a:'+ 'f'*300,'\u2000::1\ufeff','\u0085::1']
    ips += ['.'.join(str(rng.randrange(256)) for _ in range(4)) for _ in range(80)]
    ips += [':'.join(format(rng.randrange(65536),'x') for _ in range(8)) for _ in range(80)]
    nums=['0','1','4294967295','4294967296','9007199254740993','340282366920938463463374607431768211455','340282366920938463463374607431768211456','-1','1.0','+1','0x1','0b1','00000001','1\n','1\r\n','9'*400,'',' ','１２','1e2']
    cidrs=[a+'/'+b for a in ['0.0.0.0','192.168.1.7','255.255.255.255','::','::1','2001:db8::1','ffff:ffff:ffff:ffff:ffff:ffff:ffff:ffff'] for b in ['0','1','24','31','32','64','127','128','129','-1','0x10','0b10','  ','+2','01','24/ignored','1.5','NaN','Infinity','']]
    cidrs += [f'{rng.randrange(256)}.{rng.randrange(256)}.{rng.randrange(256)}.{rng.randrange(256)}/{rng.randrange(33)}' for _ in range(80)]
    result=[]
    for cmd in COMMANDS[:-1]:
        values=[None]+(nums if cmd=='long2ip' else cidrs if cmd in ['parseCIDR','isValidCIDR'] else ips)
        choices=['expanded','compressed'] if cmd=='toIPv6Expand' else ['IPv4'] if cmd=='toIPv6Format' else ['IPv4','IPv6']
        result += [dict(command=cmd,input=x,choice=c) for c in choices for x in values]
    return result
