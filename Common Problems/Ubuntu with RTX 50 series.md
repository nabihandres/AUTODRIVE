# Installing Ubuntu 22.04 on PCs with NVIDIA RTX 50 Series GPUs

This guide explains how to install **Ubuntu 22.04 LTS** on computers with **NVIDIA RTX 50 Series GPUs**, especially when the standard Ubuntu Desktop installer fails to boot correctly.

## Why this guide is needed

On some modern PCs with NVIDIA RTX 50 Series graphics cards, the Ubuntu 22.04 Desktop installer may show a black screen after selecting: "Try or Install Ubuntu".

In some cases, the system may still boot in the background, but no image is displayed. This usually happens because the Ubuntu Desktop live environment does not include a sufficiently recent NVIDIA driver for these GPUs.

## Common symptoms include:

Black screen after selecting Try or Install Ubuntu.
No image even when using Safe Graphics.
No image after adding nomodeset.
The system appears to start, but the monitor receives no usable video output.

## Why use Ubuntu Server?

Instead of using the Ubuntu Desktop installer, this guide uses Ubuntu Server 22.04.5 LTS.

Ubuntu Server uses a text-based installer, which avoids the graphical environment that causes the black screen. After the base system is installed, the NVIDIA driver can be installed from the terminal. Once the GPU is working correctly, the Ubuntu Desktop environment can be installed normally.

The final result is still a fully usable Ubuntu 22.04 desktop system, but installed through a safer path for RTX 50 Series GPUs.
# Table of Contents 
- [1. Preparing the Installation Media](#1-preparing-the-installation-media) 
  - [1.1 Download Ubuntu Server](#11-download-ubuntu-server) 
  - [1.2 Download Rufus](#12-download-rufus) 
  - [1.3 Create the Bootable USB Drive](#13-create-the-bootable-usb-drive) 
  - [1.4 Shrink the Windows Partition](#14-shrink-the-windows-partition) 
  - [1.5 Boot from the USB Drive](#15-boot-from-the-usb-drive) 
  - [1.6 Initial Ubuntu Server Configuration](#16-initial-ubuntu-server-configuration) 
- [2. Installing Ubuntu Server](#2-installing-ubuntu-server) 
  - [2.1 Manual Storage Configuration](#21-manual-storage-configuration) 
  - [2.2 Configure Ubuntu Partitions](#22-configure-ubuntu-partitions) 
  - [2.3 Create the User Account](#23-create-the-user-account) 
  - [2.4 Install OpenSSH](#24-install-openssh) 
  - [2.5 Complete the Installation](#25-complete-the-installation) 
- [3. Configuring Ubuntu Server](#3-configuring-ubuntu-server) 
  - [3.1 First Login](#31-first-login) 
  - [3.2 Update Ubuntu Server](#32-update-ubuntu-server) 
- [4. Installing NVIDIA Drivers](#4-installing-nvidia-drivers) 
  - [4.1 Install the NVIDIA Driver](#41-install-the-nvidia-driver) 
  - [4.2 Verify the Installation](#42-verify-the-installation) 
- [5. Installing Ubuntu Desktop](#5-installing-ubuntu-desktop) 
  - [5.1 Install the Desktop Environment](#51-install-the-desktop-environment) 
  - [5.2 Final Reboot](#52-final-reboot)

---

## Prerequisites

Before starting, make sure you have:

* A computer with Windows already installed.
* At least **40 GB** of unallocated disk space. **100 GB or more is recommended**.
* A USB flash drive with **8 GB** or more.
* An Internet connection.
* Rufus.

> [!WARNING]
> This guide includes manual partitioning. Selecting the wrong disk or formatting the wrong partition can erase Windows or personal data. Read each step carefully before continuing.

---

# 1. Preparing the Installation Media

This section explains how to prepare the Ubuntu Server installation USB and reserve disk space for Ubuntu from Windows before starting the installer.

The goal is to avoid using the Ubuntu Desktop live installer, which may fail on some NVIDIA RTX 50 Series systems, and instead boot into the text-based Ubuntu Server installer.

## 1.1 Download Ubuntu Server

Download the official **Ubuntu Server 22.04.5 LTS** ISO image from the Ubuntu website.

Recommended ISO:

```text
ubuntu-22.04.5-live-server-amd64.iso
````

The Server version is used because its installer does not require a graphical desktop environment. This helps avoid black screen issues caused by missing or outdated NVIDIA drivers in the live Desktop installer.

<img width="1125" height="740" alt="image" src="https://github.com/user-attachments/assets/144c9d77-9032-43d0-b655-e69567988c94" />

## 1.2 Download Rufus

Download and open **Rufus** on Windows.

Rufus will be used to create the bootable USB drive from the Ubuntu Server ISO.

<img width="767" height="757" alt="image" src="https://github.com/user-attachments/assets/695cbd61-11c7-4f8d-861e-1b3a8f5098ab" />

## 1.3 Create the Bootable USB Drive

Connect the USB flash drive to the computer and open **Rufus**.

> [!WARNING]
> The USB drive will be erased. Back up any important files before continuing.

Configure Rufus using the following settings:

| Setting          | Value                                  |
| ---------------- | -------------------------------------- |
| Device           | USB flash drive (name of your device)  |
| Boot selection   | `ubuntu-22.04.5-live-server-amd64.iso` |
| Partition scheme | **GPT**                                |
| Target system    | **UEFI (non CSM)**                     |
| File system      | **Large FAT32**                        |
| Cluster size     | **Default**                            |

If the USB drive does not appear in Rufus, press:

```text
Alt + F
```

This enables the detection of large-capacity USB storage devices.

> [!NOTE]
> Rufus hide large removable drives by default to reduce the risk of accidentally formatting the wrong device.

<img width="603" height="758" alt="image" src="https://github.com/user-attachments/assets/6dfa2c3e-5ef7-44e7-9da0-794f25b56612" />

After verifying the configuration, click:

```text
START
```

If Rufus asks how to write the image, select:

```text
Write in ISO Image mode (Recommended)
```
<img width="624" height="372" alt="image" src="https://github.com/user-attachments/assets/2f6af4c1-9dff-49d5-822a-08951be2b9c5" />

Wait until Rufus finishes creating the bootable USB.

---

## 1.4 Shrink the Windows Partition

Before booting the Ubuntu installer, reserve space for Ubuntu from Windows.

This is recommended because Windows can safely resize its own NTFS partition and reduce the chance of filesystem issues.

Open Windows Disk Management:

```text
Win + X → Disk Management
```

or search for:

```text
Create and format hard disk partitions
```

<img width="1437" height="819" alt="image" src="https://github.com/user-attachments/assets/21241a5d-324f-49c9-b9f9-29dfc3658ca0" />

Identify the Windows partition, usually labeled:

```text
C:
```

Right-click the Windows partition and select:

```text
Shrink Volume
```

Enter the amount of space to reserve for Ubuntu.

Recommended space:

| Use case                     | Suggested space |
| ---------------------------- | --------------- |
| Minimal Ubuntu installation  | 40 GB           |
| General use                  | 100 GB          |
| ROS 2 / robotics development | 150 GB or more  |

After shrinking, Windows should show a new region labeled:

```text
Unallocated
```

> [!IMPORTANT]
> Leave this space as **Unallocated**. Do not create a new partition and do not format it in Windows. Ubuntu will use this free space during manual partitioning.

https://github.com/user-attachments/assets/345fb7c9-a8d7-487e-9b15-811f49935b92

---

## 1.5 BIOS/UEFI Settings

Restart the computer and enter the BIOS/UEFI setup.

Common BIOS keys include:

| Manufacturer | BIOS/UEFI Key |
| ------------ | ------------- |
| ASUS         | Del or F2     |
| MSI          | Del           |
| Gigabyte     | Del           |
| ASRock       | Del or F2     |
| Dell         | F2            |
| HP           | Esc or F10    |
| Lenovo       | F1 or F2      |

Recommended settings:

| Setting           | Recommended value                      |
| ----------------- | -------------------------------------- |
| Boot mode         | **UEFI**                               |
| CSM / Legacy Boot | **Disabled**                           |
| Secure Boot       | **Disabled**                           |
| Fast Boot         | Optional: Disabled during installation |

> [!NOTE]
> Secure Boot can sometimes interfere with NVIDIA driver installation. It is recommended to disable it during the installation process.

Save the changes and restart the computer.

---

## 1.6 Boot from the USB Drive

With the USB drive connected, open the **Boot Menu** during startup.

Common Boot Menu keys:

| Manufacturer | Boot Menu Key |
| ------------ | ------------- |
| ASUS         | F8            |
| MSI          | F11           |
| Gigabyte     | F12           |
| ASRock       | F11           |
| Dell         | F12           |
| HP           | F9            |
| Lenovo       | F12           |

Select the USB entry that starts with:

```text
UEFI:
```

Example:

```text
UEFI: USB Flash Drive
```

https://github.com/user-attachments/assets/e60a453e-14ad-4498-ba30-61b82fe6baea

---

## 1.7 Launch the Ubuntu Server Installer

When the Ubuntu Server boot menu appears, select:

```text
Ubuntu Server with the HWE kernel
```

The **HWE kernel** is recommended because it provides newer hardware support within Ubuntu 22.04, which is useful on modern PCs.

<img width="1599" height="943" alt="WhatsApp Image 2026-06-25 at 7 31 45 PM" src="https://github.com/user-attachments/assets/a855a833-1598-47a5-983b-23a5a02ab3df" />

---

## 1.8 Initial Ubuntu Server Configuration

The installer will ask for several basic settings before storage configuration.

### Language

Select your preferred language.

### Keyboard Layout

Select the keyboard layout that matches your keyboard.

Common options include:

```text
English (US)
```

or:

```text
Spanish (Latin America)
```

### Network Configuration

If the computer is connected through Ethernet, Ubuntu should automatically detect the network.

Unless a custom configuration is required, keep the default network settings.

### Proxy Configuration

If no proxy is used, leave the field empty.

```text
(blank)
```

Select:

```text
Done
```

### Ubuntu Archive Mirror

Keep the default Ubuntu mirror.

Select:

```text
Done
```

https://github.com/user-attachments/assets/1c7c61ac-c8bd-4dbc-9126-820caa98eec6

After completing these steps, the installer will proceed to the **Storage Configuration** screen.

The next section explains how to perform manual partitioning and install Ubuntu without deleting Windows.

```

# 2. Installing Ubuntu Server

## 2.1 Manual Storage Configuration

When the installer reaches the **Storage Configuration** screen, select:

```text
Custom storage layout
```

> [!WARNING]
> **Do not select `Use entire disk`.** This option will erase Windows, all existing partitions, and every file stored on the selected drive.

### Why is manual partitioning required?

Although the installation space was previously reserved from Windows, some versions of the Ubuntu Server installer (Subiquity) may not correctly detect the unallocated region.

In this case, the partition can be created manually from the installer terminal.

Open a terminal by pressing:

```text
Ctrl + Alt + F2
```

Display the current partition table:

```bash
lsblk -o NAME,SIZE,FSTYPE,TYPE,MOUNTPOINTS
```

Then inspect the available free space:

```bash
sudo parted /dev/sdb unit GiB print free
```

> [!NOTE]
> Replace `/dev/sdb` with your system drive if it has a different device name.

Locate the **Free Space** region reported by `parted`.

Example:

<img width="1413" height="300" alt="image" src="https://github.com/user-attachments/assets/671283ee-be61-4793-a239-22eeb38e766d" />

Create the Ubuntu partition:

```bash
sudo parted /dev/sdb
```

Inside `parted`:

```bash
mkpart Ubuntu <FreeSpaceStart> <FreeSpaceEnd>
quit
```

Example:

<img width="1119" height="141" alt="image" src="https://github.com/user-attachments/assets/041a2004-2454-4c9f-ae49-418cb1c31f46" />

It is important to consider that the limits of the free space should not be included, in order to avoid overlap with other memory blocks. In the example, the previous block (812 GiB) corresponds to a storage unit on the disk, and the 932 GiB limit represents the final limit of the memory.

The error occurs when we take one of these limits, such as 932 GiB. The system warns that this last bit may not be within the usable capacity of the disk, which means that we need to select a value one GiB inside the available range to avoid problems. For a finer adjustment, we could work with MiB to avoid wasting around 2 GB of memory; however, this tutorial does not consider that level of precision.

Check that the new partition was added to the table:

```bash
print
```
<img width="1447" height="396" alt="image" src="https://github.com/user-attachments/assets/b9ebc066-1bd0-46f0-a72c-5e5ed9a28dd4" />

Reload the partition table:

```bash
sudo partprobe /dev/sdb
```

Reload the partition table:

```bash
lsblk
```

<img width="1391" height="736" alt="image" src="https://github.com/user-attachments/assets/87c3ca0a-75e0-44cf-9727-93ba8fb3fab7" />

Return to the installer:

```text
Ctrl + Alt + F1
```

or

```text
Ctrl + Alt + F3
```

depending on the virtual console where the installer is running.

https://github.com/user-attachments/assets/2125c6fa-89da-4f17-8b8a-26af2cc475e8

## 2.2 Configure Ubuntu Partitions

Once the new partition appears in the installer:

Configure it as:

| Partition | Format | Mount Point |
|-----------|--------|-------------|
| Ubuntu Partition | ext4 | `/` |

Reuse the existing EFI partition created by Windows:

| Partition | Format | Mount Point |
|-----------|--------|-------------|
| EFI System Partition | Leave formatted as VFAT | `/boot/efi` |

> [!IMPORTANT]
> Never format the existing EFI partition. Ubuntu and Windows can safely share the same EFI System Partition.

The installer should look similar to:

```text
/           → ext4
/boot/efi   → existing VFAT partition
```

https://github.com/user-attachments/assets/a8c00386-0e2e-4e0a-afff-dcfaaabc4a19

## 2.3 Create the User Account

Continue with the installation wizard.

The installer will ask for:

- Your full name.
- Username.
- Computer hostname.
- Password.

Example:

<img width="1755" height="538" alt="image" src="https://github.com/user-attachments/assets/e998b4c5-b53e-498a-ae66-9c8fef9b0439" />

Choose a secure password since it will also be used for administrative (`sudo`) privileges.

## 2.4 Install OpenSSH

When prompted:

```text
Install OpenSSH server
```

select:

```text
Yes
```

Installing OpenSSH is highly recommended because it allows remote administration through SSH if graphical issues occur later.

No optional Ubuntu Server snaps are required for this installation.

Leave all optional snaps unchecked and continue.

https://github.com/user-attachments/assets/78f314a8-bf2a-4141-a33e-c01b1ef10c8d

## 2.5 Complete the Installation

After Ubuntu Server finishes copying the files:

Select:

```text
Reboot Now
```

<img width="1600" height="1200" alt="image" src="https://github.com/user-attachments/assets/e9184937-8dcf-4bb4-b63a-9422a688c6fb" />

Remove the USB drive when prompted.

If the following message appears:

```text
Please remove the installation medium, then press ENTER
```

remove the USB flash drive and press **Enter**.

The computer should now boot into Ubuntu Server.

---

# 3. Configuring Ubuntu Server

## 3.1 First Login

After rebooting, Ubuntu Server will display:

```text
hostname login:
```

Log in using the username and password created during installation.

## 3.2 Update Ubuntu Server

Before installing the NVIDIA driver, update the operating system.

```bash
sudo apt update
sudo apt full-upgrade -y
```

If the **needrestart** dialog appears, keep the default options and press:

```text
OK
```

<img width="1200" height="1600" alt="image" src="https://github.com/user-attachments/assets/e684691d-197e-466a-9b5b-9067414841ed" />

Finally, reboot the system:

```bash
sudo reboot
```

---

# 4. Installing NVIDIA Drivers

## 4.1 Install the NVIDIA Driver

After rebooting, log in again.

Install Ubuntu's driver management utility:

```bash
sudo apt install -y ubuntu-drivers-common
```

Display the available drivers:

```bash
sudo ubuntu-drivers devices
```

Ubuntu will list all compatible NVIDIA drivers.

<img width="1600" height="1200" alt="image" src="https://github.com/user-attachments/assets/ba85b74a-39ba-4f84-9534-bf3968127092" />

Install the recommended driver.

Example:

```bash
sudo ubuntu-drivers install nvidia:580-open
```

> [!NOTE]
> The exact driver version may change over time. Always install the version recommended by `ubuntu-drivers`.

After the installation finishes:

```bash
sudo reboot
```

---

## 4.2 Verify the Installation

After rebooting:

```bash
nvidia-smi
```

A successful installation should display something similar to:

<img width="1600" height="1200" alt="image" src="https://github.com/user-attachments/assets/7852458f-83a5-4a58-a886-c03aea43b3d9" />

If the GPU appears correctly, the NVIDIA driver has been installed successfully.

> [!IMPORTANT]
> Do not install the graphical desktop environment until `nvidia-smi` works correctly.

---

# 5. Installing Ubuntu Desktop

## 5.1 Install the Desktop Environment

Once the NVIDIA driver has been verified, install the Ubuntu Desktop packages.

```bash
sudo apt install -y ubuntu-desktop
```

This package installs:

- GNOME Desktop
- GDM Display Manager
- Ubuntu graphical applications
- Desktop utilities

Depending on your Internet connection, this process may take several minutes.

<img width="1600" height="1200" alt="image" src="https://github.com/user-attachments/assets/73ce144d-cc27-4052-b0f1-532419f91216" />

## 5.2 Final Reboot

After the installation completes:

```bash
sudo reboot
```

Ubuntu should now boot directly into the graphical desktop.

<img width="1600" height="1200" alt="image" src="https://github.com/user-attachments/assets/184e7285-edf1-4fa4-823e-654f1b1d0335" />

The installation is now complete.

You should have:

- ✅ Ubuntu 22.04 Desktop
- ✅ Latest NVIDIA driver
- ✅ Fully working graphical interface
- ✅ Dual Boot with Windows
- ✅ System ready for ROS 2 Humble installation

````

