# SockScan: Scanning Networks with Socks. Why use just one sock when you have several feet?

<img src="./img/sockscan-logo.png" width="500">


Welcome to SockScan, the pentester’s best-kept secret for distributed network scanning with SOCKS proxies. Why “scan in chaussette”? Because it’s subtle, silent, and efficient, - just like socks on a hardwood floor. 🧦

Disclaimer : I designed this tool during a pentest, it is not perfect and Chatgpt was a great help to develop it quickly. Help on the project is appreciate. 

## Why This Exists

Let’s face it: using tools like nmap over SOCKS proxies can feel like trying to download the internet on a dial-up connection. (Yes you can tune your proxychains and add a lot of parameters to nmap to have better perfomance). And comparing service access results across different SOCKS servers? That’s a level of tedium we wouldn’t wish on anyone.

This tool tackles these issues head-on by:
- Easy to use.

- Speeding up scans by distributing tasks across multiple proxies, multithread and specify a custom timeout.

- Enhancing stealth by spreading requests over different SOCKS servers. You are in redteam and you have already pwn some servers? Use me to distribute the scan to these pivots and reduce the noise on the network.

- Automating the comparison of service availability across proxy endpoints. Are you sure all your pivot have the same network access ? Now you can test it !

## How It Works

You provide a list of targets and SOCKS proxy servers. You should deploy Socks proxy, i can't do it for you :) 

The tool splits the workload, distributing scans across the proxies if you set it in the single mode, otherwise in the per_proxy mode it will share the same target list for each proxy.



## Installation
You should have python3 on your machine. 
Socks Proxy Server(s) on your pivot(s)

```bash
git clone https://github.com/MarcrowProject/SockScan.git
cd SockScan
pip install -r requirements.txt
```

## Usage
1. Edit the config.json file 
2. Specify target inside targets.txt
3. Execute the scan

```bash
python sockScan.py
```

# Contributing

Feel like contributing? Awesome! Open a pull request or create an issue to discuss your ideas. Whether it’s bug fixes, new features, or documentation improvements, all help is welcome.

# Disclaimer

This tool is for ethical use only. Ensure you have proper authorization before scanning any network. Misuse of this tool can lead to serious consequences. The authors are not responsible for any illegal activity performed using this software.




