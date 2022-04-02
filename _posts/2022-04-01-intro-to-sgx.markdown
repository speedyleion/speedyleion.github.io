---
layout: post
title:  "Intro to Intel SGX"
date:   2022-04-01 18:40:03 -0700
categories: sgx c++
---

I have a need to dig into Intel SGX, so thought I would document my adventure.
This is mostly going to be a re-hashing of Intel docs so there probably isn't
going to be anything new or enlightening in this post.

Brief "what is SGX"
===================

SGX stands for "Software Guard Extensions".  This is Intel's implementation of a
[TEE][TEE].  A TEE is a "Trusted Execution Environment".  A TEE allows code to
be encrypted and run in a way that is protected from other processes on the CPU
seeing what exactly the code does.  

This is a poor summary, but this post is about utilizing SGX not defining it.

Intel Docs
==========

Intel has documentation on how to get started with SGX.  
_I found it was hard to separate the "how to" from the "marketing"_

My desire was to utilize linux, ubuntu in this case.

The [Intel Technical Library][Intel Technical Library] has some documents, but
when I went looking I didn't see the linux installation docs.  I also found the
[SGX Overview][SGX Overview] page.  This page had some links
for linux things. At first glance this looked like it just linked to some
binaries, "Prebuilt Binary Downloads".  Navigating through the folders in
those prebuilt binaries there is a "Documentation" folder which houses the
[installation guide for linux][Installation Guide For Linux].


First Installation attempt
--------------------------

We start like most ubuntu software installs start:

```
sudo apt update
sudo apt upgrade
```

The [installation guide for linux][Installation Guide For Linux] mentions three
different drivers. I chose the DCAP one.

```
sudo apt-get install build-essential ocaml automake autoconf libtool wget python libssl-dev dkms
```

Even though the link says `server` it works for desktop versions and WSL

```
wget - https://download.01.org/intel-sgx/latest/linux-latest/distro/ubuntu20.04-server/sgx_linux_x64_driver_1.41.bin
chmod 777 sgx_linux_x64_driver_1.41.bin
sudo ./sgx_linux_x64_driver_1.41.bin
```

And this is where things started to go wrong for me.  I was using WSL2 so I ran into this:

```
Error! Your kernel headers for kernel 4.19.128-microsoft-standard cannot be found.
Please install the linux-headers-4.19.128-microsoft-standard package,
```

### WSL2 Kernel detour

`sudo apt-get install linux-headers-4.19.128-microsoft-standard` won't fix the
problem.  It took a bit of digging but I eventually found,
[https://centerorbit.medium.com/installing-wireguard-in-wsl-2-dd676520cb21](https://centerorbit.medium.com/installing-wireguard-in-wsl-2-dd676520cb21)
with some good instructions to get past the missing headers issue. However,
the instructions for checking out the branch are no longer valid.  Through all
of this rigamarol and investigation I ended up updating my WSL2 kernel.  I'll
skip those instructions and provide a link,
[https://github.com/microsoft/WSL/issues/5650#issuecomment-765825503](https://github.com/microsoft/WSL/issues/5650#issuecomment-765825503.).
You shouldn't need to update your kernel, but I was pulling levers to try to get
things moving.

```
sudo apt-get install bison build-essential flex libssl-dev libelf-dev bc pkg-config dwarves
git clone --branch linux-msft-wsl-5.10.y --depth 1 https://github.com/microsoft/WSL2-Linux-Kernel.git
cd WSL2-Linux-Kernel
zcat /proc/config.gz > .config
make -j $(nproc)  
cd /lib/modules
sudo ln -s 5.10.102.1-microsoft-standard-WSL2+/ 5.10.102.1-microsoft-standard-WSL2
```

> One would use branch `linux-msft-wsl-4.19.y` if the error message was about
> 4.19.128

re-ran `sudo ./sgx_linux_x64_driver_1.41.bin` and got 
```
'make' KDIR=/lib/modules/5.10.102.1-microsoft-standard-WSL2/build...(bad exit status: 2)
ERROR (dkms apport): binary package for sgx: 1.41 not found
Error! Bad return status for module build on kernel: 5.10.102.1-microsoft-standard-WSL2 (x86_64)
Consult /var/lib/dkms/sgx/1.41/build/make.log for more information.
```

Looking in `/var/lib/dkms/sgx/1.41/build/make.log` I found:

```
/var/lib/dkms/sgx/1.41/build/main.c:775:3: error: #error "kernel version is not be supported. We need either mmput_async or kallsyms_lookup_name exported from kernel"
  775 |  #error "kernel version is not be supported. We need either mmput_async or kallsyms_lookup_name exported from kernel"
      |   ^~~~~
```
This is probably becuase I updated the kernel :(.

Second Installation Attempt
---------------------------

I decided to utilize the out of tree (OOT) driver since my new kernel version
didn't seem to work with the DCAP version.

Per the instructions on
[https://github.com/intel/linux-sgx-driver](https://github.com/intel/linux-sgx-driver)
you will most likely still need to build the headers, 
[WSL2 Kernel Detour](#wsl2-kernel-detour).

```
sudo apt update
sudo apt upgrade
sudo apt-get install build-essential ocaml automake autoconf libtool wget python libssl-dev dkms
wget - https://download.01.org/intel-sgx/latest/linux-latest/distro/ubuntu20.04-server/sgx_linux_x64_driver_2.11.0_2d2b795.bin
chmod 777 sgx_linux_x64_driver_2.11.0_2d2b795.bin
sudo ./sgx_linux_x64_driver_2.11.0_2d2b795.bin
```

Success!!!

Building Test Application
-------------------------

With the SGX driver installed I wanted to run a test application. First I needed
to get all of the SDK and packages

```
echo 'deb [arch=amd64] https://download.01.org/intel-sgx/sgx_repo/ubuntu focal main' | sudo tee /etc/apt/sources.list.d/intel-sgx.list
wget -qO - https://download.01.org/intel-sgx/sgx_repo/ubuntu/intel-sgx-deb.key | sudo apt-key add
sudo apt-get update
sudo apt-get install libsgx-epid libsgx-quote-ex libsgx-dcap-ql libsgx-urts-dbgsym libsgx-enclave-common-dbgsym libsgx-dcap-ql-dbgsym libsgx-dcap-default-qpl-dbgsym libsgx-enclave-common-dev libsgx-dcap-ql-dev libsgx-dcap-default-qpl-dev
wget - https://download.01.org/intel-sgx/latest/linux-latest/distro/ubuntu20.04-server/sgx_linux_x64_sdk_2.15.101.1.bin
chmod +x sgx_linux_x64_sdk_2.15.101.1.bin
sudo ./sgx_linux_x64_sdk_2.15.101.1.bin --prefix /opt/intel
```

Then I cloned
[https://github.com/intel/linux-sgx.git](https://github.com/intel/linux-sgx.git)
and navigated to `SampleCode/SampleEnclave`.  There is a `README.txt` in there.
The bare `make` invocation will result in building a HW debug version, so I gave
it a try.  It compiled fine, but when I went to run the app, I got.

```
$ ./app
Info: Please make sure SGX module is enabled in the BIOS, and install SGX driver afterwards.
Error: Invalid SGX device.
Enter a character before exit ...
```

### Checking for SGX support

Really I should have done this first, but you know...

There is a nice test app that someone wrote,
[https://github.com/ayeks/SGX-hardware#test-sgx](https://github.com/ayeks/SGX-hardware#test-sgx).

```
clang test-sgx.c -o test-sgx
./test-sgx
```
And my output
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

Fail whale :(, no HW sgx on my machine.  Or is there...

Machines that support SGX have 3 possible states in their bios:

  - SGX Disabled
  - SGX Enabled
  - SGX Software controlled

My machine happened to be set to software controlled. One can enable SGX via an app,
[https://www.intel.com/content/www/us/en/support/articles/000058952/software/intel-security-products.html](https://www.intel.com/content/www/us/en/support/articles/000058952/software/intel-security-products.html).  

> To be honest I'm not sure what advantage this has over just flipping the state in the bios manually.

After installing the app, running it as an administrator and rebooting:

```
sgx available: 0
sgx launch control: 0

CPUID Leaf 12H, Sub-Leaf 0 of Intel SGX Capabilities (EAX=12H,ECX=0)
eax: 0 ebx: 0 ecx: 0 edx: 0
sgx 1 supported: 0
sgx 2 supported: 0
MaxEnclaveSize_Not64: 0
MaxEnclaveSize_64: 0
```

However this was WSL, as part of my debugging I also built the `test-sgx` for
native windows.  Running the test in a native windows command prompt:

```
sgx available: 1
sgx launch control: 1

CPUID Leaf 12H, Sub-Leaf 0 of Intel SGX Capabilities (EAX=12H,ECX=0)
eax: 1 ebx: 0 ecx: 0 edx: 241f
sgx 1 supported: 1
sgx 2 supported: 0
MaxEnclaveSize_Not64: 1f
MaxEnclaveSize_64: 24
```

So it looks like I have HW SGX and it's available in windows, but might not be
available through WSL.

Summary
=======

This post is already pretty long so I'll stop here.  Unfortunatly I don't have
HW SGX working via WSL.  I'll try to do some more digging and see if I can get
it working with WSL, otherwise I may just need to punt and utilize the windows
SDKs for HW usage.


[TEE]: https://en.wikipedia.org/wiki/Trusted_execution_environment
[Intel Technical Library]: https://www.intel.com/content/www/us/en/developer/library.html?s=Newest&f:@stm_10309_en=[Intel%C2%AE%20Software%20Guard%20Extensions%20(Intel%C2%AE%20SGX)]
[SGX Overview]: https://www.intel.com/content/www/us/en/developer/tools/software-guard-extensions/overview.html
[Installation Guide For Linux]: https://download.01.org/intel-sgx/sgx-linux/2.15.1/docs/Intel_SGX_SW_Installation_Guide_for_Linux.pdf