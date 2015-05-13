# vim: ts=2 sw=2 et ft=ruby

Vagrant.configure("2") do |config|
  config.vm.synced_folder ".", "/vagrant", disabled: true
  config.ssh.username = "root"
  [
    "debian_wheezy", "debian_jessie", "ubuntu_trusty",
    "centos_7", "fedora_21",
  ].each do |vmname|
    config.vm.define vmname do |vm|
      vm.vm.provider "docker" do |docker|
        docker.build_dir = "images/#{vmname}"
        docker.has_ssh = true
      end
    end
  end
end
