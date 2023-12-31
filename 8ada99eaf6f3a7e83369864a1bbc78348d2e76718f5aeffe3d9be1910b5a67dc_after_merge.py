    def get_tor_paths(self):
        if self.platform == "Linux":
            tor_path = shutil.which("tor")
            if not tor_path:
                raise CannotFindTor()
            obfs4proxy_file_path = shutil.which("obfs4proxy")
            prefix = os.path.dirname(os.path.dirname(tor_path))
            tor_geo_ip_file_path = os.path.join(prefix, "share/tor/geoip")
            tor_geo_ipv6_file_path = os.path.join(prefix, "share/tor/geoip6")
        elif self.platform == "Windows":
            base_path = self.get_resource_path("tor")
            tor_path = os.path.join(base_path, "Tor", "tor.exe")
            obfs4proxy_file_path = os.path.join(base_path, "Tor", "obfs4proxy.exe")
            tor_geo_ip_file_path = os.path.join(base_path, "Data", "Tor", "geoip")
            tor_geo_ipv6_file_path = os.path.join(base_path, "Data", "Tor", "geoip6")
        elif self.platform == "Darwin":
            tor_path = shutil.which("tor")
            if not tor_path:
                raise CannotFindTor()
            obfs4proxy_file_path = shutil.which("obfs4proxy")
            prefix = os.path.dirname(os.path.dirname(tor_path))
            tor_geo_ip_file_path = os.path.join(prefix, "share/tor/geoip")
            tor_geo_ipv6_file_path = os.path.join(prefix, "share/tor/geoip6")
        elif self.platform == "BSD":
            tor_path = "/usr/local/bin/tor"
            tor_geo_ip_file_path = "/usr/local/share/tor/geoip"
            tor_geo_ipv6_file_path = "/usr/local/share/tor/geoip6"
            obfs4proxy_file_path = "/usr/local/bin/obfs4proxy"

        return (
            tor_path,
            tor_geo_ip_file_path,
            tor_geo_ipv6_file_path,
            obfs4proxy_file_path,
        )