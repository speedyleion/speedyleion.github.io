---
layout: post
title:  "Get SGX working in WSL (Intro to Intel SGX part 2)"
date:   2022-04-02 12:10:03 -0700
categories: sgx c++
---

This is a continuation of 
[Intro to Intel SGX]({% post_url 2022-04-01-intro-to-sgx %})
where I had failed to get SGX working correctly in WSL.

I saw 2 options:

- Find a 16lb or 20lb sledge hammer and take out my frustration on my laptop
- Reinstall WSL and try again with the Intel DCAP driver

Less Nuclear Option
====================

I chose to take the less damaging route and try to re-install WSL to get it in a state that the Intel DCAP driver might work.

Remove WSL
----------

I found a link here, 
[https://pureinfotech.com/uninstall-wsl2-windows-10/](https://pureinfotech.com/uninstall-wsl2-windows-10/)
with instructions to remove WSL.

The steps are as follows (I wish there is a nice CLI way to do this, but windows
CLI is something I'm not fluent in).

1. Settings -> Apps & Features -> Uninstall all linux distros
2. Settings -> Apps & Features -> Uninstall "Windows Subsystem for Linux Update"
3. Settings -> Apps & Features -> Related Settings -> Programs and Features -> Turn Windows features on or off -> Uncheck "Virtual Machine Platform"
4. Settings -> Apps & Features -> Related Settings -> Programs and Features -> Turn Windows features on or off -> Uncheck "Windows Subsystem"
5. Restart

Re-install WSL
--------------

In an admin powershell console.

```
wsl --install
```

Restart.  

> The restart is important.  I tried powering down and turning back on,
but it skipped the necessary update steps

```
wsl --install -d Ubuntu-20.04
```

Unfortunately this left me with an error, 

> Error: 0x800701bc WSL 2 requires an update to its kernel component. For information please visit https://aka.ms/wsl2kernel

Doing some googling, the right thing to do is to go to the provided link and run
the "WSL2 Linux kernel update package for x64 machines" found on the page.  After
running this installer and re-attempting the `wsl --install -d Ubuntu-20.04`, I
had a running instance of Ubuntu WSL again.

Doing `uname -r` provided me with:

```
$ uname -r
5.10.16.3-microsoft-standard-WSL2
```

So clearly the `uninstall` didn't uninstall everything :(.


I spun in circles for a bit, then I eventually tried,
`Settings -> Apps & Features -> Uninstall "Windows Subsystem for Linux Update"`.
This left wsl in a state where it wouldn't start.  I then grabbed the 5.4.91
kernel package from,
[https://www.catalog.update.microsoft.com/Search.aspx?q=wsl](https://www.catalog.update.microsoft.com/Search.aspx?q=wsl).
After running the 5.4.91 installer I got:

```
$ uname -r
5.4.91-microsoft-standard-WSL2
```

This didn't put me back to the `4.19.128-microsoft-standard` kernel, but it got
me to a version that might work with the DCAP driver.

Re-trying the DCAP driver
=========================

First build the necessary kernel headers.

```
sudo apt update
sudo apt upgrade
sudo apt-get install build-essential ocaml automake autoconf libtool wget python libssl-dev dkms bison libelf-dev bc pkg-config dwarves
git clone --branch linux-msft-wsl-5.4.y --depth 1 https://github.com/microsoft/WSL2-Linux-Kernel.git
cd WSL2-Linux-Kernel
zcat /proc/config.gz > .config
make -j $(nproc)  
sudo make -j $(nproc) modules_install
cd /lib/modules
sudo ln -s 5.4.91-microsoft-standard-WSL2+/ 5.4.91-microsoft-standard-WSL2
```

Navigate back to a less privileged directory. I used the home dir. 

This will install the driver and build and run the `test-sgx` app.

```
wget - https://download.01.org/intel-sgx/latest/linux-latest/distro/ubuntu20.04-server/sgx_linux_x64_driver_1.41.bin
chmod a+x sgx_linux_x64_driver_1.41.bin
sudo ./sgx_linux_x64_driver_1.41.bin
echo 'deb [arch=amd64] https://download.01.org/intel-sgx/sgx_repo/ubuntu focal main' | sudo tee /etc/apt/sources.list.d/intel-sgx.list
wget -qO - https://download.01.org/intel-sgx/sgx_repo/ubuntu/intel-sgx-deb.key | sudo apt-key add
sudo apt-get update
sudo apt-get install libsgx-epid libsgx-quote-ex libsgx-dcap-ql libsgx-urts-dbgsym libsgx-enclave-common-dbgsym libsgx-dcap-ql-dbgsym libsgx-dcap-default-qpl-dbgsym libsgx-enclave-common-dev libsgx-dcap-ql-dev libsgx-dcap-default-qpl-dev
wget - https://download.01.org/intel-sgx/latest/linux-latest/distro/ubuntu20.04-server/sgx_linux_x64_sdk_2.15.101.1.bin
chmod +x sgx_linux_x64_sdk_2.15.101.1.bin
sudo ./sgx_linux_x64_sdk_2.15.101.1.bin --prefix /opt/intel
source /opt/intel/sgxsdk/environment
wget https://raw.githubusercontent.com/ayeks/SGX-hardware/master/test-sgx.c
clang test-sgx.c -o test-sgx
./test-sgx
```

The `test-sgx` run resulted in:
```
Extended feature bits (EAX=07H, ECX=0H)
eax: 0 ebx: 9c27a9 ecx: 0 edx: bc000000
sgx available: 0
sgx launch control: 0

CPUID Leaf 12H, Sub-Leaf 0 of Intel SGX Capabilities (EAX=12H,ECX=0)
eax: 0 ebx: 0 ecx: 0 edx: 0
sgx 1 supported: 0
sgx 2 supported: 0
MaxEnclaveSize_Not64: 0
MaxEnclaveSize_64: 0
```

Still no SGX in WSL :(

Punting on HW SGX
==================

At this point I punted on HW builds and chose to try sim builds with the
_SampleEnclave_ provided by Intel.
```
git clone https://github.com/intel/linux-sgx.git
cd linux-sgx/SampleCode/SampleEnclave
make SGX_MODE=SIM
./app
```

And I got:
```
Checksum(0x0x7ffc94a22cb0, 100) = 0xfffd4143
Info: executing thread synchronization, please wait...
Info: SampleEnclave successfully returned.
Enter a character before exit ...
```

Summary
=======

I spun my wheels a bit trying to get access to HW SGX in WSL.  There may
still be a way to get it working, but I think for now I should accept SW
simulation and move forward with the rest of my investigation desires.

Maybe it's just [sour grapes](https://www.read.gov/aesop/005.html) on my part,
but with Intel removing SGX on newer Core CPU's, it's probably not worth while to
spend too much effort making HW SGX work on an older Core CPU. See 
[12th Generation Intel Core Processors Datasheet, Volume 1 of 2](https://cdrdv2.intel.com/v1/dl/getContent/655258)
for "Deprecated Technologies".
I still have need to dig into and understand SGX, I just won't fight making it
work on HW in WSL for my I7.