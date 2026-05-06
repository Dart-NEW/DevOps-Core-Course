# Pulumi (Lab 4)

## Prerequisites
- Pulumi CLI installed
- Python 3.11+ available
- Yandex Cloud auth configured in environment

## Setup
```bash
cd pulumi
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

pulumi login
pulumi stack init dev
cp Pulumi.dev.yaml.example Pulumi.dev.yaml
# fill real values in Pulumi.dev.yaml
```

## Run
```bash
pulumi preview
pulumi up
```

## Outputs
```bash
pulumi stack output vmPublicIp
pulumi stack output sshCommand
```

## Destroy
```bash
pulumi destroy
```

## Notes
- Keep `Pulumi.dev.yaml` out of git (may include secrets)
- Use `pulumi config set --secret` for sensitive values if needed
