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
        if ['debian_jessie', 'centos_7', 'fedora_21'].include? vmname
          docker.create_args = ["-h", vmname, "-v", "/sys/fs/cgroup:/sys/fs/cgroup:ro", "--privileged"]
        else
          docker.create_args = ["-h", vmname]
        end
      end
    end
  end
end
