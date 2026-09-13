# Benchmark

Baseline usado para comparar com o RF-DETR na Fase 1.

O Ultralytics YOLO é distribuído sob AGPL-3.0. Para não misturar essa licença com o código do
projeto (MIT), ele fica isolado nesta pasta: nada em `src/pitchlens` importa o Ultralytics.

```bash
pip install -e ".[bench]"
python scripts/benchmark/train_yolo.py --model yolo26m.pt --epochs 60
```

A comparação entre os modelos é feita por `scripts/evaluate.py`, que avalia todos no mesmo
split de teste e com o mesmo cálculo de mAP.
