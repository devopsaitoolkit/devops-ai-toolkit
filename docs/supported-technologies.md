# Supported technologies

The deterministic engine reasons about the technologies below. Coverage comes from the packaged
[knowledge base](knowledge-base.md) of YAML signatures plus auto-detection of technology and input
shape. Coverage grows over time — and you can [add your own signatures](knowledge-base.md#adding-a-signature).

## Technologies (`Technology` enum)

| Value            | Area                                  |
|------------------|---------------------------------------|
| `docker`         | Docker engine / containers            |
| `docker_compose` | Docker Compose                        |
| `kubernetes`     | Kubernetes                            |
| `openshift`      | OpenShift                             |
| `terraform`      | Terraform / IaC                       |
| `ansible`        | Ansible                               |
| `openstack`      | OpenStack (Nova, Neutron, etc.)       |
| `linux`          | Generic Linux                         |
| `systemd`        | systemd units and journald            |
| `gitlab_ci`      | GitLab CI/CD                          |
| `prometheus`     | Prometheus                            |
| `grafana`        | Grafana                               |
| `rabbitmq`       | RabbitMQ                              |
| `redis`          | Redis                                 |
| `nginx`          | NGINX                                 |
| `apache`         | Apache httpd                          |
| `postgresql`     | PostgreSQL                            |
| `mysql`          | MySQL / MariaDB                       |
| `ceph`           | Ceph storage                         |
| `linstor`        | LINSTOR / DRBD                        |
| `vmware`         | VMware                                |
| `aws`            | Amazon Web Services                   |
| `azure`          | Microsoft Azure                       |
| `gcp`            | Google Cloud Platform                 |
| `unknown`        | Fallback when detection is inconclusive |

You can always pass a hint (`--tech` on the CLI, `technology=` in the SDK, `"technology"` in the
API) to skip auto-detection.

## Input shapes (`SourceKind` enum)

The engine also classifies the *shape* of the input, which signatures target via `applies_to`:

| Value                 | Meaning                                  |
|-----------------------|-------------------------------------------|
| `log`                 | Application / system log                  |
| `yaml`                | Generic YAML                              |
| `terraform`           | Terraform configuration or output         |
| `compose`             | Docker Compose file                       |
| `kubernetes_manifest` | A Kubernetes manifest                     |
| `command_output`      | Output captured from a command            |
| `error_string`        | A single error name or message            |
| `unknown`             | Fallback                                  |

## Knowledge-base files

Each technology area maps to a YAML data file under `knowledge/data/`, including: `kubernetes.yaml`,
`terraform.yaml`, `docker.yaml`, `openstack.yaml`, `linux.yaml`, `systemd.yaml`, `nginx.yaml`,
`postgresql.yaml`, `mysql.yaml`, `redis.yaml`, `rabbitmq.yaml`, `prometheus.yaml`, `ceph.yaml`,
`ansible.yaml`, `gitlab_ci.yaml`, `aws.yaml`, `azure_gcp.yaml`.

See exactly what is installed in your version:

```bash
devops-ai list                 # all signatures
devops-ai list --tech kubernetes
```

## Example coverage (Kubernetes)

A few of the catalogued Kubernetes signatures:

- `k8s.crashloopbackoff` — Pod in CrashLoopBackOff
- `k8s.imagepullbackoff` — ImagePullBackOff / ErrImagePull
- `k8s.oomkilled` — Container OOMKilled (exit code 137)

```bash
devops-ai explain CrashLoopBackOff
devops-ai explain ImagePullBackOff
devops-ai explain OOMKilled
```

## Requesting or adding coverage

- Open an issue describing the error pattern and a sample input.
- Or contribute a signature yourself — it's just YAML. See
  [Contributing](contributing.md) and [Knowledge base](knowledge-base.md).

More worked troubleshooting guides for these technologies live at
<https://devopsaitoolkit.com/blog>.
