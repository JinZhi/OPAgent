function FindProxyForURL(url, host) {
	ogilvy_bej = "PROXY 10.172.1.45:81; DIRECT";
	ogilvy_sha = "PROXY 10.173.2.10:3128; DIRECT";
	ogilvy_gzh = "PROXY 10.176.1.20:3128; DIRECT";
	ogilvy_fzh = "PROXY 10.188.1.12:3128; DIRECT";
	google_cn = "PROXY 127.0.0.1:9999; DIRECT";
	DEFAULT = "DIRECT";
	if (dnsDomainIs(host, '.google.com') ||
	    dnsDomainIs(host, 'google.com') ||
	    dnsDomainIs(host, '.ggpht.com') ||
	    dnsDomainIs(host, 'appspot.com') ||
	    dnsDomainIs(host, '.appspot.com') ||
	    dnsDomainIs(host, '.blogspot.com') ||
	    dnsDomainIs(host, '.google.cn') ||
	    dnsDomainIs(host, '.gstatic.cn') ||
	    dnsDomainIs(host, '.google.com.hk') ||
	    dnsDomainIs(host, '.googlesource.com') ||
	    dnsDomainIs(host, '.keyhole.com') ||
	    dnsDomainIs(host, '.angrybirds.com') ||
	    dnsDomainIs(host, 'chromium.org') ||
	    dnsDomainIs(host, '.chromium.org') ||
	    dnsDomainIs(host, '.android.com') ||
	    dnsDomainIs(host, '.chrome.com') ||
	    dnsDomainIs(host, '.googlesyndication.com') ||
	    dnsDomainIs(host, '.googlelabs.com') ||
	    dnsDomainIs(host, '.feedburner.coms') ||
	    dnsDomainIs(host, 'g.co') ||
	    dnsDomainIs(host, 'gmail.com') ||
	    dnsDomainIs(host, 'goo.gl') ||
	    dnsDomainIs(host, '.gmail.com') ||
	    dnsDomainIs(host, '.googlemail.com') ||
	    dnsDomainIs(host, '.google-analytics.com') ||
	    dnsDomainIs(host, '.googleadservices.com') ||
	    dnsDomainIs(host, '.panoramio.com') ||
	    dnsDomainIs(host, '.googleusercontent.com') ||
	    dnsDomainIs(host, '.gstatic.com') ||
	    dnsDomainIs(host, '.googleapis.com') ||
	    dnsDomainIs(host, '.googlecode.com') ||
	    dnsDomainIs(host, '.ogilvy.com'))
	{
		if (isInNet(myIpAddress(), "10.172.0.0", "255.255.0.0")) return ogilvy_bej;
		if (isInNet(myIpAddress(), "10.173.0.0", "255.255.0.0")) return ogilvy_sha;
		if (isInNet(myIpAddress(), "10.176.0.0", "255.255.0.0")) return ogilvy_gzh;
		if (isInNet(myIpAddress(), "10.188.0.0", "255.255.0.0")) return ogilvy_fzh;
		return google_cn;
	}
	if (isInNet(myIpAddress(), "10.172.0.0", "255.255.0.0")) return ogilvy_bej;
	if (isInNet(myIpAddress(), "10.173.0.0", "255.255.0.0")) return ogilvy_sha;
	if (isInNet(myIpAddress(), "10.176.0.0", "255.255.0.0")) return ogilvy_gzh;
	if (isInNet(myIpAddress(), "10.188.0.0", "255.255.0.0")) return ogilvy_fzh;
	return DEFAULT;
}
