# -*- mode: ruby -*-
# vi: set ft=ruby :
VAGRANTFILE_API_VERSION = "2"

Vagrant.configure(VAGRANTFILE_API_VERSION) do |config|
  config.vm.box = "ubuntu/xenial64"
  config.vm.network :private_network, ip: "192.168.10.100"

  config.vm.provider :virtualbox do |vb|
    vb.customize ["modifyvm", :id, "--name", "app-backend", "--memory", "1536"]
  end

  # Shared folder from the host machine to the guest machine. Uncomment the line
  # below to enable it.
  #config.vm.synced_folder "../../../my-cool-app", "/webapps/mycoolapp/my-cool-app"

  # Ansible provisioner.
  config.vm.provision "ansible" do |ansible|
    ansible.playbook = "vagrant.yml"
    ansible.host_key_checking = false
    ansible.verbose = "vv"
  end
end
