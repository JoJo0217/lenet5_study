import torch
from torch import nn
import torch.nn.functional as F


# resnet paper https://arxiv.org/abs/1512.03385 -> option A, B
class ResBlock(nn.Module):
    def __init__(self, in_channel, out_channel, is_downsample=False):
        super().__init__()
        self.is_downsample = is_downsample
        stride = 2 if is_downsample else 1
        # conv2d 기본적으로 he uniform initialization을 사용하기에 따로 설정 x
        self.seq = nn.Sequential(
            nn.Conv2d(in_channel, out_channel, kernel_size=3,
                      stride=stride, padding=1, bias=False,),
            nn.BatchNorm2d(out_channel),
            nn.ReLU(),
            nn.Conv2d(out_channel, out_channel, kernel_size=3,
                      stride=1, padding=1, bias=False,),
            nn.BatchNorm2d(out_channel),
        )

        # option B: downsample -> shortcut을 cnn으로 구현
        if self.is_downsample:
            self.downsample = nn.Sequential(
                nn.Conv2d(in_channel, out_channel, kernel_size=1,
                          stride=stride, bias=False),
                nn.BatchNorm2d(out_channel),
            )
        else:
            self.downsample = nn.Identity()

    def forward(self, x):
        # option A: stride 2로 선택
        return F.relu(self.seq(x) + self.downsample(x))


class Resnet18(nn.Module):
    def __init__(self, class_num=10):
        super().__init__()
        self.seq = nn.Sequential(
            nn.Conv2d(3, 64, kernel_size=3, stride=1, padding=1, bias=False),
            nn.BatchNorm2d(64),
            nn.ReLU(),
            ResBlock(64, 64),        # 64, 32x32유지
            ResBlock(64, 64),        # 64, 32x32유지
            ResBlock(64, 128, is_downsample=True),                # 128, 16x16
            ResBlock(128, 128),
            ResBlock(128, 256, is_downsample=True),                # 256, 8x8
            ResBlock(256, 256),
            ResBlock(256, 512, is_downsample=True),                # 512, 4x4
            ResBlock(512, 512),
            nn.AdaptiveAvgPool2d((1, 1))  # 512, 1x1
        )
        self.flat = nn.Flatten()
        self.out = nn.Linear(512, class_num)

    def forward(self, x):
        x = self.seq(x)
        return self.out(self.flat(x))

    def extract_features(self, x):
        return self.flat(self.seq(x))


class ResBottleNeckBlock(nn.Module):
    def __init__(self, in_channel, out_channel, is_downsample=False, stride=None):
        super().__init__()
        if stride is None:
            self.stride = 2 if is_downsample else 1
        else:
            self.stride = stride
        self.in_channel = in_channel
        self.out_channel = out_channel

        mid_channel = out_channel // 4
        self.seq = nn.Sequential(
            nn.Conv2d(in_channel, mid_channel, kernel_size=1, bias=False),
            nn.BatchNorm2d(mid_channel),
            nn.ReLU(),
            nn.Conv2d(mid_channel, mid_channel, kernel_size=3,
                      stride=self.stride, padding=1, bias=False),
            nn.BatchNorm2d(mid_channel),
            nn.ReLU(),
            nn.Conv2d(mid_channel, out_channel, kernel_size=1, bias=False),
            nn.BatchNorm2d(out_channel),
        )

        if is_downsample:
            self.downsample = self._identitymap
        else:
            self.downsample = nn.Identity()

    def forward(self, x):
        return F.relu(self.seq(x) + self.downsample(x))

    def _identitymap(self, x):
        x = x[:, :, ::self.stride, ::self.stride]
        dim = self.out_channel // self.in_channel  # in_channel을 out_channel로 만들어야함
        for _ in range(dim // 2):  # 2배 -> 1번 4배 -> 2번
            x = torch.concat((x, torch.zeros_like(x)), dim=1)
        return x


class ResBottleNecknet18(nn.Module):
    def __init__(self, class_num=10):
        super().__init__()
        self.seq = nn.Sequential(
            nn.Conv2d(3, 64, kernel_size=3, stride=1, padding=1, bias=False),
            nn.BatchNorm2d(64),
            nn.ReLU(),
            ResBottleNeckBlock(64, 256, is_downsample=True, stride=1),
            ResBottleNeckBlock(256, 256),
            ResBottleNeckBlock(256, 512, is_downsample=True),
            ResBottleNeckBlock(512, 512),
            ResBottleNeckBlock(512, 1024, is_downsample=True),
            ResBottleNeckBlock(1024, 1024),
            ResBottleNeckBlock(1024, 2048, is_downsample=True),
            ResBottleNeckBlock(2048, 2048),
            nn.AvgPool2d(4),
        )
        self.flat = nn.Flatten()
        self.out = nn.Linear(2048, class_num)

    def forward(self, x):
        x = self.seq(x)
        return self.out(self.flat(x))

    def extract_features(self, x):
        return self.flat(self.seq(x))


class ResBottleNecknet50(nn.Module):
    def __init__(self, class_num=10):
        super().__init__()
        self.seq = nn.Sequential(
            nn.Conv2d(3, 64, kernel_size=3, stride=1, padding=1, bias=False),
            nn.BatchNorm2d(64),
            nn.ReLU(),
            ResBottleNeckBlock(64, 256, is_downsample=True, stride=1),
            ResBottleNeckBlock(256, 256),
            ResBottleNeckBlock(256, 256),
            ResBottleNeckBlock(256, 512, is_downsample=True),
            ResBottleNeckBlock(512, 512),
            ResBottleNeckBlock(512, 512),
            ResBottleNeckBlock(512, 512),
            ResBottleNeckBlock(512, 1024, is_downsample=True),
            ResBottleNeckBlock(1024, 1024),
            ResBottleNeckBlock(1024, 1024),
            ResBottleNeckBlock(1024, 1024),
            ResBottleNeckBlock(1024, 1024),
            ResBottleNeckBlock(1024, 1024),
            ResBottleNeckBlock(1024, 2048, is_downsample=True),
            ResBottleNeckBlock(2048, 2048),
            ResBottleNeckBlock(2048, 2048),
            nn.AvgPool2d(4),
        )
        self.flat = nn.Flatten()
        self.out = nn.Linear(2048, class_num)

    def forward(self, x):
        x = self.seq(x)
        return self.out(self.flat(x))

    def extract_features(self, x):
        return self.flat(self.seq(x))


# preactive paper https://arxiv.org/abs/1603.05027 -> option preactive
class PreActResBlock(nn.Module):
    def __init__(self, in_channel, out_channel, is_downsample=False):
        super().__init__()
        stride = 2 if is_downsample else 1

        self.seq = nn.Sequential(
            nn.BatchNorm2d(in_channel),
            nn.ReLU(),
            nn.Conv2d(in_channel, out_channel, kernel_size=3,
                      stride=stride, padding=1, bias=False,),
            nn.BatchNorm2d(out_channel),
            nn.ReLU(),
            nn.Conv2d(out_channel, out_channel, kernel_size=3,
                      stride=1, padding=1, bias=False,),
        )
        if is_downsample:
            self.downsample = self._identitymap
        else:
            self.downsample = nn.Identity()

    def forward(self, x):
        return self.seq(x) + self.downsample(x)
        # identity map을 downsample하는 함수

    def _identitymap(self, x):
        x = x[:, :, ::2, ::2]
        y = torch.zeros_like(x)
        return torch.concat((x, y), dim=1)


class PreActResNet(nn.Module):
    def __init__(self, class_num=10):
        super().__init__()
        self.seq = nn.Sequential(
            nn.Conv2d(3, 64, kernel_size=3, stride=1, padding=1, bias=False),
            nn.ReLU(),
            PreActResBlock(64, 64),
            PreActResBlock(64, 64),
            PreActResBlock(64, 128, is_downsample=True),
            PreActResBlock(128, 128),
            PreActResBlock(128, 256, is_downsample=True),
            PreActResBlock(256, 256),
            PreActResBlock(256, 512, is_downsample=True),
            PreActResBlock(512, 512),
            nn.ReLU(),
            nn.AvgPool2d(4),
        )
        self.flat = nn.Flatten()
        self.out = nn.Linear(512, class_num)

    def forward(self, x):
        x = self.seq(x)
        return self.out(self.flat(x))

    def extract_features(self, x):
        return self.flat(self.seq(x))

# resnext paperhttps://arxiv.org/pdf/1611.05431


class ResNextBlock(nn.Module):
    def __init__(self, in_channel, inner_channel, out_channel, cardinality=32, is_downsample=False, stride=None):
        super().__init__()
        if stride is None:
            stride = 2 if is_downsample else 1
        self.seq = nn.Sequential(
            nn.Conv2d(in_channel, inner_channel, kernel_size=1, bias=False),
            nn.BatchNorm2d(inner_channel),
            nn.ReLU(),
            nn.Conv2d(inner_channel, inner_channel, kernel_size=3,
                      stride=stride, padding=1, groups=cardinality, bias=False),
            nn.BatchNorm2d(inner_channel),
            nn.ReLU(),
            nn.Conv2d(inner_channel, out_channel, kernel_size=1, bias=False),
            nn.BatchNorm2d(out_channel),
        )

        if is_downsample:
            self.downsample = nn.Sequential(
                nn.Conv2d(in_channel, out_channel, kernel_size=1,
                          stride=stride, bias=False),
                nn.BatchNorm2d(out_channel),
            )
        else:
            self.downsample = nn.Identity()

    def forward(self, x):
        return F.relu(self.seq(x) + self.downsample(x))


class ResNext(nn.Module):
    def __init__(self, class_num=10):
        super().__init__()
        self.seq = nn.Sequential(
            nn.Conv2d(3, 64, kernel_size=3, stride=1, padding=1,
                      bias=False),  # 3,32,32 -> 64,32,32
            nn.BatchNorm2d(64),
            nn.ReLU(),
            ResNextBlock(64, 128, 256, is_downsample=True,
                         stride=1),     # 256,32,32 -> feature size를 유지하고 64를 256으로 증가시키기 위함
            ResNextBlock(256, 128, 256),
            ResNextBlock(256, 256, 512, is_downsample=True),  # 512 16x16
            ResNextBlock(512, 256, 512),
            ResNextBlock(512, 512, 1024, is_downsample=True),  # 1024 8x8
            ResNextBlock(1024, 512, 1024),
            ResNextBlock(1024, 1024, 2048, is_downsample=True),  # 2048 4x4
            ResNextBlock(2048, 1024, 2048),
            nn.AvgPool2d(4),
        )
        self.flat = nn.Flatten()
        self.out = nn.Linear(2048, class_num)

    def forward(self, x):
        x = self.seq(x)
        return self.out(self.flat(x))

    def extract_features(self, x):
        return self.flat(self.seq(x))


# convnext paper: https://arxiv.org/pdf/2201.03545


class ConvNeXtblock(nn.Module):
    def __init__(self, channel):
        super().__init__()
        self.depth_wise = nn.Conv2d(channel, channel, kernel_size=7,
                                    padding=3, groups=channel)
        self.norm = nn.LayerNorm(channel)
        self.point_wise1 = nn.Conv2d(channel, channel * 4, kernel_size=1)
        self.gelu = nn.GELU()
        self.point_wise2 = nn.Conv2d(channel * 4, channel, kernel_size=1)

        nn.init.zeros_(self.point_wise2.weight)
        if self.point_wise2.bias is not None:
            nn.init.zeros_(self.point_wise2.bias)

    def forward(self, x):
        residual = x
        x = self.depth_wise(x)
        x = x.permute(0, 2, 3, 1)  # BCWH -> BWHC
        x = self.norm(x)
        x = x.permute(0, 3, 1, 2)  # BWHC -> BCWH
        x = self.point_wise1(x)
        x = self.gelu(x)
        x = self.point_wise2(x)
        return x + residual


class ConvNeXt(nn.Module):
    def __init__(self, class_num=10):
        super().__init__()
        self.seq = nn.Sequential(
            # 원본은 kernel 4 stride 4 지금은 2 2로 변경
            nn.Conv2d(3, 96, kernel_size=2, stride=2, padding=0,
                      bias=False),  # 3x32x32 -> 96x16x16
            # 블럭 비율 1:1:3:1 -> 2:2:6:2
            ConvNeXtblock(96),
            ConvNeXtblock(96),
            nn.Conv2d(96, 192, kernel_size=2, stride=2),
            ConvNeXtblock(192),  # 96x16x16 -> 192x8x8
            ConvNeXtblock(192),
            nn.Conv2d(192, 384, kernel_size=2, stride=2),
            ConvNeXtblock(384,),  # 192x8x8 -> 384x4x4
            ConvNeXtblock(384,),
            ConvNeXtblock(384,),
            ConvNeXtblock(384,),
            ConvNeXtblock(384,),
            ConvNeXtblock(384,),
            nn.Conv2d(384, 768, kernel_size=2, stride=2),
            ConvNeXtblock(768),  # 384x4x4 -> 768x2x2
            ConvNeXtblock(768),
            nn.AvgPool2d(2),  # 768x2x2 -> 768x1x1
        )
        self.flat = nn.Flatten()
        self.out = nn.Linear(768, class_num)

    def forward(self, x):
        x = self.seq(x)
        return self.out(self.flat(x))

    def extract_features(self, x):
        return self.flat(self.seq(x))
