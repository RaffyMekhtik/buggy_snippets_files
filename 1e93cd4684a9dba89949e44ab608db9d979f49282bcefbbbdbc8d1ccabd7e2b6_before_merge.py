def get_web_screenshots(target, scan_id, proctimeout):
    scan_dir = utils.get_scan_dir(scan_id)
    xml_file = os.path.join(scan_dir, f"nmap.{scan_id}.xml")
    outFiles = os.path.join(scan_dir, f"aquatone.{scan_id}")
    output = []
    logger.info(f"Attempting to take screenshots for {target}")

    aquatoneArgs = ["aquatone", "-nmap", "-scan-timeout", "2500", "-out", outFiles]
    with open(xml_file, "r") as f:
        process = subprocess.Popen(
            aquatoneArgs, stdin=f, stdout=subprocess.DEVNULL
        )  # nosec

    try:
        process.communicate(timeout=proctimeout)
        if process.returncode == 0:
            time.sleep(
                0.5
            )  # a small sleep to make sure all file handles are closed so that the agent can read them
    except subprocess.TimeoutExpired:
        logger.warning(f"TIMEOUT: Killing aquatone against {target}")
        process.kill()

    session_path = os.path.join(outFiles, "aquatone_session.json")
    if not os.path.isfile(session_path):
        return output

    with open(session_path) as f:
        session = json.load(f)

    if session["stats"]["screenshotSuccessful"] > 0:
        logger.info(
            f"{target} - Success: {session['stats']['screenshotSuccessful']}, Fail: {session['stats']['screenshotFailed']}"
        )

        for k, page in session["pages"].items():
            fqScreenshotPath = os.path.join(outFiles, page["screenshotPath"])
            if page["hasScreenshot"] and os.path.isfile(fqScreenshotPath):
                urlp = urlparse(page["url"])
                if not urlp.port and urlp.scheme == "http":
                    port = 80
                elif not urlp.port and urlp.scheme == "https":
                    port = 443
                else:
                    port = urlp.port
                logger.info(
                    f"{urlp.scheme.upper()} screenshot acquired for {page['hostname']} on port {port}"
                )
                output.append(
                    {
                        "host": page["hostname"],
                        "port": port,
                        "service": urlp.scheme.upper(),
                        "data": base64_image(fqScreenshotPath),
                    }
                )
    return output