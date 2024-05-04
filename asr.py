from bcut_asr_branch import run_everywhere
from argparse import Namespace


f = open("./input/test01.mp4", "rb")
argg = Namespace(format="srt", interval=30.0, input=f, output=None)
run_everywhere(argg)