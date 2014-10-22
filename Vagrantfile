# -*- mode: ruby -*-
# vi: set ft=ruby :

## this Vagrantfile requires the "VirtualBox <version> Oracle VM VirtualBox Extension Pack"
## https://www.virtualbox.org/wiki/Downloads

# Vagrantfile API/syntax version. Don't touch unless you know what you're doing!
VAGRANTFILE_API_VERSION = "2"

Vagrant.configure(VAGRANTFILE_API_VERSION) do |config|
    # Every Vagrant virtual environment requires a box to build off of.
    config.vm.box = "ubuntu/trusty64"

    # Disable automatic box update checking. If you disable this, then
    # boxes will only be checked for updates when the user runs
    # `vagrant box outdated`. This is not recommended.
    # config.vm.box_check_update = false

    # Create a forwarded port mapping which allows access to a specific port
    # within the machine from a port on the host machine. In the example below,
    # accessing "localhost:8080" will access port 80 on the guest machine.
    # config.vm.network "forwarded_port", guest: 80, host: 8080

    # Create a private network, which allows host-only access to the machine
    # using a specific IP.
    # config.vm.network "private_network", ip: "192.168.33.10"

    # Create a public network, which generally matched to bridged network.
    # Bridged networks make the machine appear as another physical device on
    # your network.
    # config.vm.network "public_network"

    # If true, then any SSH connections made will enable agent forwarding.
    # Default value: false
    config.ssh.forward_agent = true
    
    # Share an additional folder to the guest VM. The first argument is
    # the path on the host to the actual folder. The second argument is
    # the path on the guest to mount the folder. And the optional third
    # argument is a set of non-required options.
    # config.vm.synced_folder "../data", "/vagrant_data"

    config.vm.provider "virtualbox" do |vb|
        # Don't boot with headless mode
        vb.gui = true

        vb.customize ["modifyvm", :id, "--memory", "1024"]
        
        ## add a USB interface to this VM.
        vb.customize ["modifyvm", :id, "--usb", "on"]
        vb.customize ["modifyvm", :id, "--usbehci", "on"]
        
        ## @todo add usb device filter for RCP
        # vb.customize [
        #     "usbfilter", "add", "0",
        #     "--target", :id,
        #     "--name", "Great Scott Gadgets HackRF [0100]",
        #     "--vendorid", "0x1D50",
        #     "--product", "0x604B",
        # ]
    end
    
    config.vm.provision "shell", privileged: false, path: "vagrant_provision.sh"
end
