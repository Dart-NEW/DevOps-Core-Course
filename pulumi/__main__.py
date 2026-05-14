import pulumi
import pulumi_yandex as yandex

config = pulumi.Config()

project_name = config.get("projectName") or "devops-core"
zone = config.get("zone") or "ru-central1-a"
subnet_cidr = config.get("subnetCidr") or "10.10.0.0/24"
allowed_ssh_cidr = config.require("allowedSshCidr")
ssh_username = config.get("sshUsername") or "ubuntu"
ssh_public_key = config.require("sshPublicKey")
image_family = config.get("imageFamily") or "ubuntu-2404-lts"

image = yandex.get_compute_image(family=image_family)

network = yandex.VpcNetwork(
    f"{project_name}-network",
    name=f"{project_name}-network",
    labels={"project": project_name, "lab": "lab04", "tool": "pulumi"},
)

subnet = yandex.VpcSubnet(
    f"{project_name}-subnet",
    name=f"{project_name}-subnet",
    network_id=network.id,
    zone=zone,
    v4_cidr_blocks=[subnet_cidr],
)

security_group = yandex.VpcSecurityGroup(
    f"{project_name}-sg",
    name=f"{project_name}-sg",
    network_id=network.id,
    ingresses=[
        {
            "description": "SSH from trusted CIDR",
            "protocol": "TCP",
            "port": 22,
            "v4_cidr_blocks": [allowed_ssh_cidr],
        },
        {
            "description": "HTTP",
            "protocol": "TCP",
            "port": 80,
            "v4_cidr_blocks": [allowed_ssh_cidr],
        },
        {
            "description": "Custom app port",
            "protocol": "TCP",
            "port": 5000,
            "v4_cidr_blocks": [allowed_ssh_cidr],
        },
    ],
    egresses=[
        {
            "description": "Allow all outbound traffic",
            "protocol": "ANY",
            "from_port": 0,
            "to_port": 65535,
            "v4_cidr_blocks": ["0.0.0.0/0"],
        }
    ],
)

instance = yandex.ComputeInstance(
    f"{project_name}-vm",
    name=f"{project_name}-vm",
    hostname=f"{project_name}-vm",
    platform_id="standard-v2",
    zone=zone,
    resources={
        "cores": 2,
        "memory": 1,
        "core_fraction": 20,
    },
    boot_disk={
        "initialize_params": {
            "image_id": image.id,
            "size": 10,
            "type": "network-hdd",
        }
    },
    network_interfaces=[
        {
            "subnet_id": subnet.id,
            "nat": True,
            "security_group_ids": [security_group.id],
        }
    ],
    metadata={
        "ssh-keys": f"{ssh_username}:{ssh_public_key}",
    },
    labels={"project": project_name, "lab": "lab04", "tool": "pulumi"},
)

public_ip = instance.network_interfaces[0].nat_ip_address
internal_ip = instance.network_interfaces[0].ip_address

pulumi.export("vmPublicIp", public_ip)
pulumi.export("vmInternalIp", internal_ip)
pulumi.export("sshCommand", public_ip.apply(lambda ip: f"ssh {ssh_username}@{ip}"))
