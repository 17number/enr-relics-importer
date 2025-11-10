import csv
import difflib
import math
import os
import re
import sys
import unicodedata
from datetime import datetime

import cv2
import numpy as np


def resource_path(relative_path):
    """PyInstaller でも開発環境でも同じようにパスを解決"""
    base_path = getattr(sys, '_MEIPASS', os.path.abspath("."))
    path = os.path.join(base_path, relative_path)
    # 外部動画(relics.mp4)などは、同梱に失敗する可能性があるのでカレントも探す
    if not os.path.exists(path):
        alt_path = os.path.join(os.path.dirname(sys.executable), relative_path)
        if os.path.exists(alt_path):
            return alt_path
    return path

def imread_unicode(path, flags=cv2.IMREAD_GRAYSCALE):
    with open(path, 'rb') as f:
        bytes_data = f.read()
    img_array = np.frombuffer(bytes_data, np.uint8)
    return cv2.imdecode(img_array, flags)

# === 設定 ===
VIDEO_PATH = resource_path("relics.mp4")
LABELED_BASE = resource_path("labeled_chars")
NAME_DIR = os.path.join(LABELED_BASE, "name")
EFFECT_DIR = os.path.join(LABELED_BASE, "effect")
output_dir = os.path.join(
    os.path.dirname(sys.executable)
        if getattr(sys, 'frozen', False)
        else os.path.abspath("output")
)
os.makedirs(output_dir, exist_ok=True)
CSV_PATH = os.path.join(
    output_dir,
    f"relics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
)

FRAME_SKIP_DIFF_TH = 1.75
CALC_BASE_WIDTH = 3840
CALC_BASE_HEIGHT = 2160
CALC_BASE_RELIC_NAME_CHAR_WIDTH = 50
CALC_BASE_RELIC_EFFECT_CHAR_WIDTH = 40

RELIC_NAME_CHARS = 15
RELIC_EFFECT_CHARS = 40

EFFECT_LIST = [
    "【レディ】アーツ発動中、敵撃破で攻撃力上昇",
    "【レディ】スキルのダメージ上昇",
    "【レディ】スキル使用時、僅かに無敵",
    "【レディ】生命力／筋力上昇、精神力低下",
    "【レディ】精神力／信仰上昇、知力低下",
    "【レディ】短剣による連続攻撃時、周囲の敵に、直近の出来事を再演",
    "【レディ】背後からの致命の一撃後、自身の姿を見え難くし、足音を消す",
    "【隠者】アーツ発動時、最大ＨＰ上昇",
    "【隠者】アーツ発動時、自身が出血状態になり、攻撃力上昇",
    "【隠者】生命力／持久力／技量上昇、知力／信仰低下",
    "【隠者】属性痕を集めた時、「魔術の地」が発動",
    "【隠者】属性痕を集めた時、対応する属性カット率上昇",
    "【隠者】知力／信仰上昇、精神力低下",
    "【執行者】アーツ発動中、咆哮でＨＰ回復",
    "【執行者】アビリティ発動時、ＨＰをゆっくりと回復",
    "【執行者】スキル中、妖刀が解放状態になるとＨＰ回復",
    "【執行者】スキル中の攻撃力上昇、攻撃時にＨＰ減少",
    "【執行者】技量／神秘上昇、生命力低下",
    "【執行者】生命力／持久力上昇、神秘低下",
    "【守護者】アーツ発動時、周囲の味方のＨＰを徐々に回復",
    "【守護者】アビリティ発動中、ガード成功時、衝撃波が発生",
    "【守護者】スキルの持続時間延長",
    "【守護者】スキル使用時、周囲の味方のカット率上昇",
    "【守護者】筋力／技量上昇、生命力低下",
    "【守護者】精神力／信仰上昇、生命力低下",
    "【守護者】斧槍タメ攻撃時、つむじ風が発生",
    "【追跡者】アーツ発動時、周囲を延焼",
    "【追跡者】アビリティ発動時、アーツゲージ増加",
    "【追跡者】スキルに、出血の状態異常を付加",
    "【追跡者】スキルの使用回数＋１",
    "【追跡者】スキル使用時、通常攻撃で炎を纏った追撃を行う（大剣のみ）",
    "【追跡者】精神力上昇、生命力低下",
    "【追跡者】知力／信仰上昇、筋力／技量低下",
    "【鉄の目】アーツのタメ発動時、毒の状態異常を付加",
    "【鉄の目】アーツ発動後、刺突カウンター強化",
    "【鉄の目】スキルに毒の状態異常を付加して毒状態の敵に大ダメージ",
    "【鉄の目】スキルの使用回数＋１",
    "【鉄の目】弱点の持続時間を延長させる",
    "【鉄の目】神秘上昇、技量低下",
    "【鉄の目】生命力／筋力上昇、技量低下",
    "【復讐者】アーツ発動時、ファミリーと味方を強化",
    "【復讐者】アーツ発動時、自身のＨＰと引き換えに周囲の味方のＨＰを全回復",
    "【復讐者】アーツ発動時、霊炎の爆発を発生",
    "【復讐者】アビリティ発動時、最大ＦＰ上昇",
    "【復讐者】ファミリーと共闘中の間、自身を強化",
    "【復讐者】筋力上昇、信仰低下",
    "【復讐者】生命力／持久力上昇、精神力低下",
    "【無頼漢】アーツの効果時間延長",
    "【無頼漢】スキル中に攻撃を受けると攻撃力と最大スタミナ上昇",
    "【無頼漢】スキル命中時、敵の攻撃力低下",
    "【無頼漢】神秘上昇、生命力低下",
    "【無頼漢】精神力／知力上昇、生命力／持久力低下",
    "ＨＰ持続回復",
    "ＨＰ低下時、カット率上昇",
    "ＨＰ低下時、カット率上昇",
    "ＨＰ低下時、周囲の味方を含めＨＰをゆっくりと回復",
    "ＨＰ低下時、周囲の味方を含めＨＰをゆっくりと回復",
    "アーツゲージ蓄積増加＋１",
    "アーツゲージ蓄積増加＋２",
    "アーツゲージ蓄積増加＋３",
    "アイテムの効果が周囲の味方にも発動",
    "アイテムの効果が周囲の味方にも発動",
    "ガードカウンターに、自身の現在ＨＰの一部を加える",
    "ガードカウンターに、自身の現在ＨＰの一部を加える",
    "ガードカウンター強化",
    "ガードカウンター強化",
    "ガードカウンター強化＋１",
    "ガードカウンター強化＋２",
    "ガード成功時、ＨＰを回復",
    "ガード成功時、ＨＰを回復",
    "ガード成功時、アーツゲージを蓄積",
    "ガード成功時、アーツゲージを蓄積",
    "ガード成功時、アーツゲージを蓄積＋１",
    "ガード中、敵に狙われやすくなる",
    "ガード中、敵に狙われやすくなる",
    "カーリアの剣の魔術を強化",
    "カーリアの剣の魔術を強化",
    "ジェスチャー「あぐら」により、発狂が蓄積",
    "スキルクールタイム軽減＋１",
    "スキルクールタイム軽減＋２",
    "スキルクールタイム軽減＋３",
    "ダメージで吹き飛ばされた時、強靭度とカット率上昇",
    "ダメージで吹き飛ばされた時、強靭度とカット率上昇",
    "ダメージを受けた直後、攻撃によりＨＰの一部を回復",
    "ダメージを受けた直後、攻撃によりＨＰの一部を回復",
    "ダメージを受けた直後、攻撃によりＨＰの一部を回復＋１",
    "ダメージを受けた直後、攻撃によりＨＰの一部を回復＋２",
    "トーテム・ステラの周囲で、強靭度上昇",
    "トーテム・ステラの周囲で敵を倒した時、ＨＰ回復",
    "フレイルの攻撃でＦＰ回復",
    "フレイルの攻撃でＦＰ回復",
    "フレイルの攻撃でＨＰ回復",
    "フレイルの攻撃でＨＰ回復",
    "フレイルの攻撃力上昇",
    "フレイルの攻撃力上昇",
    "フレイルの武器種を３つ以上装備していると攻撃力上昇",
    "フレイルの武器種を３つ以上装備していると攻撃力上昇",
    "遺跡の強敵を倒す度、神秘上昇",
    "茨の魔術を強化",
    "茨の魔術を強化",
    "炎カット率上昇",
    "炎カット率上昇",
    "炎カット率上昇＋１",
    "炎カット率上昇＋２",
    "炎攻撃力上昇",
    "炎攻撃力上昇",
    "炎攻撃力上昇＋１",
    "炎攻撃力上昇＋１",
    "炎攻撃力上昇＋２",
    "炎攻撃力上昇＋２",
    "炎攻撃力上昇＋３",
    "炎攻撃力上昇＋４",
    "王都古竜信仰の祈祷を強化",
    "王都古竜信仰の祈祷を強化",
    "黄金律原理主義の祈祷を強化",
    "黄金律原理主義の祈祷を強化",
    "鎌の攻撃でＦＰ回復",
    "鎌の攻撃でＦＰ回復",
    "鎌の攻撃でＨＰ回復",
    "鎌の攻撃でＨＰ回復",
    "鎌の攻撃力上昇",
    "鎌の攻撃力上昇",
    "鎌の武器種を３つ以上装備していると攻撃力上昇",
    "鎌の武器種を３つ以上装備していると攻撃力上昇",
    "祈祷強化",
    "祈祷強化＋１",
    "祈祷強化＋２",
    "輝剣の魔術を強化",
    "輝剣の魔術を強化",
    "輝石、重力石アイテムの攻撃力上昇",
    "輝石、重力石アイテムの攻撃力上昇",
    "輝石、重力石アイテムの攻撃力上昇＋１",
    "技量＋１",
    "技量＋２",
    "技量＋３",
    "弓の攻撃でＦＰ回復",
    "弓の攻撃でＦＰ回復",
    "弓の攻撃でＨＰ回復",
    "弓の攻撃でＨＰ回復",
    "弓の攻撃力上昇",
    "弓の攻撃力上昇",
    "弓の武器種を３つ以上装備していると攻撃力上昇",
    "弓の武器種を３つ以上装備していると攻撃力上昇",
    "巨人の火の祈祷を強化",
    "巨人の火の祈祷を強化",
    "強靭度＋１",
    "強靭度＋２",
    "強靭度＋３",
    "強靭度＋３",
    "狂い火の祈祷を強化",
    "狂い火の祈祷を強化",
    "曲剣の攻撃でＦＰ回復",
    "曲剣の攻撃でＦＰ回復",
    "曲剣の攻撃でＨＰ回復",
    "曲剣の攻撃でＨＰ回復",
    "曲剣の攻撃力上昇",
    "曲剣の攻撃力上昇",
    "曲剣の武器種を３つ以上装備していると攻撃力上昇",
    "曲剣の武器種を３つ以上装備していると攻撃力上昇",
    "筋力＋１",
    "筋力＋２",
    "筋力＋３",
    "結晶人の魔術を強化",
    "結晶人の魔術を強化",
    "拳の攻撃でＦＰ回復",
    "拳の攻撃でＦＰ回復",
    "拳の攻撃でＨＰ回復",
    "拳の攻撃でＨＰ回復",
    "拳の攻撃力上昇",
    "拳の攻撃力上昇",
    "拳の武器種を３つ以上装備していると攻撃力上昇",
    "拳の武器種を３つ以上装備していると攻撃力上昇",
    "抗死耐性上昇",
    "抗死耐性上昇",
    "抗死耐性上昇＋１",
    "攻撃を受けると攻撃力上昇",
    "攻撃命中時、スタミナ回復",
    "攻撃命中時、スタミナ回復",
    "攻撃命中時、スタミナ回復＋１",
    "攻撃連続時、ＦＰ回復",
    "最大ＦＰ上昇",
    "最大ＦＰ上昇",
    "最大ＨＰ上昇",
    "最大ＨＰ上昇",
    "最大スタミナ上昇",
    "最大スタミナ上昇",
    "刺剣の攻撃でＦＰ回復",
    "刺剣の攻撃でＦＰ回復",
    "刺剣の攻撃でＨＰ回復",
    "刺剣の攻撃でＨＰ回復",
    "刺剣の攻撃力上昇",
    "刺剣の攻撃力上昇",
    "刺剣の武器種を３つ以上装備していると攻撃力上昇",
    "刺剣の武器種を３つ以上装備していると攻撃力上昇",
    "刺突カウンター発生時、ＨＰ回復",
    "刺突カウンター発生時、ＨＰ回復",
    "刺突カウンター発生時、ＨＰ回復＋１",
    "脂アイテム使用時、追加で物理攻撃力上昇",
    "脂アイテム使用時、追加で物理攻撃力上昇",
    "脂アイテム使用時、追加で物理攻撃力上昇＋１",
    "脂アイテム使用時、追加で物理攻撃力上昇＋２",
    "持久力＋１",
    "持久力＋２",
    "持久力＋３",
    "自身と味方の取得ルーン増加",
    "自身と味方の取得ルーン増加",
    "自身を除く、周囲の味方のスタミナ回復速度上昇",
    "自身を除く、周囲の味方のスタミナ回復速度上昇",
    "周囲で睡眠状態の発生時、攻撃力上昇",
    "周囲で睡眠状態の発生時、攻撃力上昇＋１",
    "周囲で凍傷状態の発生時、自身の姿を隠す",
    "周囲で毒／腐敗状態の発生時、攻撃力上昇",
    "周囲で発狂状態の発生時、攻撃力上昇",
    "周囲で発狂状態の発生時、攻撃力上昇＋１",
    "獣の祈祷を強化",
    "獣の祈祷を強化",
    "重刺剣の攻撃でＦＰ回復",
    "重刺剣の攻撃でＦＰ回復",
    "重刺剣の攻撃でＨＰ回復",
    "重刺剣の攻撃でＨＰ回復",
    "重刺剣の攻撃力上昇",
    "重刺剣の攻撃力上昇",
    "重刺剣の武器種を３つ以上装備していると攻撃力上昇",
    "重刺剣の武器種を３つ以上装備していると攻撃力上昇",
    "重力の魔術を強化",
    "重力の魔術を強化",
    "出撃時に「スローイングダガー」を持つ",
    "出撃時に「炎纏いの割れ雫」を持つ",
    "出撃時に「鉛色の硬雫」を持つ",
    "出撃時に「火炎壺」を持つ",
    "出撃時に「火花の香り」を持つ",
    "出撃時に「火脂」を持つ",
    "出撃時に「塊の重力石」を持つ",
    "出撃時に「岩棘の割れ雫」を持つ",
    "出撃時に「狂熱の香薬」を持つ",
    "出撃時に「屑輝石」を持つ",
    "出撃時に「結晶投げ矢」を持つ",
    "出撃時に「高揚の香り」を持つ",
    "出撃時に「骨の毒投げ矢」を持つ",
    "出撃時に「細枝の割れ雫」を持つ",
    "出撃時に「酸の噴霧」を持つ",
    "出撃時に「呪霊喚びの鈴」を持つ",
    "出撃時に「盾脂」を持つ",
    "出撃時に「小さなポーチ」を持つ",
    "出撃時に「小さなポーチ」を持つ",
    "出撃時に「真珠色の硬雫」を持つ",
    "出撃時に「真珠色の泡雫」を持つ",
    "出撃時に「星光の欠片」を持つ",
    "出撃時に「聖脂」を持つ",
    "出撃時に「聖水壺」を持つ",
    "出撃時に「聖纏いの割れ雫」を持つ",
    "出撃時に「青色の結晶雫」を持つ",
    "出撃時に「青色の秘雫」を持つ",
    "出撃時に「石剣の鍵」を持つ",
    "出撃時に「石剣の鍵」を持つ",
    "出撃時に「大棘の割れ雫」を持つ",
    "出撃時に「鉄壺の香薬」を持つ",
    "出撃時に「毒の噴霧」を持つ",
    "出撃時に「破裂した結晶雫」を持つ",
    "出撃時に「斑彩色の硬雫」を持つ",
    "出撃時に「緋溢れの結晶雫」を持つ",
    "出撃時に「緋色の結晶雫」を持つ",
    "出撃時に「緋色の泡雫」を持つ",
    "出撃時に「緋色渦の泡雫」を持つ",
    "出撃時に「緋湧きの結晶雫」を持つ",
    "出撃時に「風の結晶雫」を持つ",
    "出撃時に「魔力脂」を持つ",
    "出撃時に「魔力纏いの割れ雫」を持つ",
    "出撃時に「魔力壺」を持つ",
    "出撃時に「誘惑の枝」を持つ",
    "出撃時に「雷脂」を持つ",
    "出撃時に「雷纏いの割れ雫」を持つ",
    "出撃時に「雷壺」を持つ",
    "出撃時に「緑湧きの結晶雫」を持つ",
    "出撃時に「連棘の割れ雫」を持つ",
    "出撃時の武器に炎攻撃力を付加",
    "出撃時の武器に出血の状態異常を付加",
    "出撃時の武器に聖攻撃力を付加",
    "出撃時の武器に毒の状態異常を付加",
    "出撃時の武器に魔力攻撃力を付加",
    "出撃時の武器に雷攻撃力を付加",
    "出撃時の武器に冷気の状態異常を付加",
    "出撃時の武器の戦技を「アローレイン」にする",
    "出撃時の武器の戦技を「クイックステップ」にする",
    "出撃時の武器の戦技を「グラビタス」にする",
    "出撃時の武器の戦技を「デターミネーション」にする",
    "出撃時の武器の戦技を「炎撃」にする",
    "出撃時の武器の戦技を「我慢」にする",
    "出撃時の武器の戦技を「祈りの一撃」にする",
    "出撃時の武器の戦技を「輝剣の円陣」にする",
    "出撃時の武器の戦技を「血の刃」にする",
    "出撃時の武器の戦技を「聖なる刃」にする",
    "出撃時の武器の戦技を「切腹」にする",
    "出撃時の武器の戦技を「霜踏み」にする",
    "出撃時の武器の戦技を「毒の霧」にする",
    "出撃時の武器の戦技を「毒蛾は二度舞う」にする",
    "出撃時の武器の戦技を「白い影の誘い」にする",
    "出撃時の武器の戦技を「溶岩噴火」にする",
    "出撃時の武器の戦技を「雷撃斬」にする",
    "出撃時の武器の戦技を「落雷」にする",
    "出撃時の武器の戦技を「嵐脚」にする",
    "出撃時の武器の戦技を「冷気の霧」にする",
    "出撃中、ショップでの購入に必要なルーンが割引",
    "出撃中、ショップでの購入に必要なルーンが割引",
    "出撃中、ショップでの購入に必要なルーンが大割引",
    "出血耐性上昇",
    "出血耐性上昇",
    "出血耐性上昇＋１",
    "小砦の強敵を倒す度、取得ルーン増加、発見力上昇",
    "小盾の武器種を３つ以上装備していると最大ＨＰ上昇",
    "小盾の武器種を３つ以上装備していると最大ＨＰ上昇",
    "消費ＦＰ軽減",
    "杖の武器種を３つ以上装備していると最大ＦＰ上昇",
    "杖の武器種を３つ以上装備していると最大ＦＰ上昇",
    "信仰＋１",
    "信仰＋２",
    "信仰＋３",
    "神狩りの祈祷を強化",
    "神狩りの祈祷を強化",
    "神秘＋１",
    "神秘＋２",
    "神秘＋３",
    "睡眠耐性上昇",
    "睡眠耐性上昇",
    "睡眠耐性上昇＋１",
    "生命力＋１",
    "生命力＋２",
    "生命力＋３",
    "精神力＋１",
    "精神力＋２",
    "精神力＋３",
    "聖カット率上昇",
    "聖カット率上昇",
    "聖カット率上昇＋１",
    "聖カット率上昇＋２",
    "聖印の武器種を３つ以上装備していると最大ＦＰ上昇",
    "聖印の武器種を３つ以上装備していると最大ＦＰ上昇",
    "聖攻撃力上昇",
    "聖攻撃力上昇",
    "聖攻撃力上昇＋１",
    "聖攻撃力上昇＋１",
    "聖攻撃力上昇＋２",
    "聖攻撃力上昇＋２",
    "聖攻撃力上昇＋３",
    "聖攻撃力上昇＋４",
    "聖杯瓶の回復を、周囲の味方に分配",
    "聖杯瓶の回復を、周囲の味方に分配",
    "聖杯瓶の回復量上昇",
    "石掘りの魔術を強化",
    "石掘りの魔術を強化",
    "潜在する力から、クロスボウを見つけやすくなる",
    "潜在する力から、バリスタを見つけやすくなる",
    "潜在する力から、フレイルを見つけやすくなる",
    "潜在する力から、鎌を見つけやすくなる",
    "潜在する力から、弓を見つけやすくなる",
    "潜在する力から、曲剣を見つけやすくなる",
    "潜在する力から、拳を見つけやすくなる",
    "潜在する力から、刺剣を見つけやすくなる",
    "潜在する力から、重刺剣を見つけやすくなる",
    "潜在する力から、小盾を見つけやすくなる",
    "潜在する力から、杖を見つけやすくなる",
    "潜在する力から、聖印を見つけやすくなる",
    "潜在する力から、槍を見つけやすくなる",
    "潜在する力から、大弓を見つけやすくなる",
    "潜在する力から、大曲剣を見つけやすくなる",
    "潜在する力から、大剣を見つけやすくなる",
    "潜在する力から、大盾を見つけやすくなる",
    "潜在する力から、大槍を見つけやすくなる",
    "潜在する力から、大槌を見つけやすくなる",
    "潜在する力から、大斧を見つけやすくなる",
    "潜在する力から、短剣を見つけやすくなる",
    "潜在する力から、中盾を見つけやすくなる",
    "潜在する力から、直剣を見つけやすくなる",
    "潜在する力から、槌を見つけやすくなる",
    "潜在する力から、爪を見つけやすくなる",
    "潜在する力から、刀を見つけやすくなる",
    "潜在する力から、特大剣を見つけやすくなる",
    "潜在する力から、特大武器を見つけやすくなる",
    "潜在する力から、斧を見つけやすくなる",
    "潜在する力から、斧槍を見つけやすくなる",
    "潜在する力から、鞭を見つけやすくなる",
    "潜在する力から、両刃剣を見つけやすくなる",
    "槍の攻撃でＦＰ回復",
    "槍の攻撃でＦＰ回復",
    "槍の攻撃でＨＰ回復",
    "槍の攻撃でＨＰ回復",
    "槍の攻撃力上昇",
    "槍の攻撃力上昇",
    "槍の武器種を３つ以上装備していると攻撃力上昇",
    "槍の武器種を３つ以上装備していると攻撃力上昇",
    "属性カット率上昇",
    "属性カット率上昇＋１",
    "属性カット率上昇＋２",
    "属性攻撃力が付加された時、属性攻撃力上昇",
    "属性攻撃力上昇",
    "属性攻撃力上昇＋１",
    "属性攻撃力上昇＋２",
    "苔薬などのアイテム使用でＨＰ回復",
    "苔薬などのアイテム使用でＨＰ回復",
    "苔薬などのアイテム使用でＨＰ回復＋１",
    "大教会の強敵を倒す度、最大ＨＰ上昇",
    "大曲剣の攻撃でＦＰ回復",
    "大曲剣の攻撃でＦＰ回復",
    "大曲剣の攻撃でＨＰ回復",
    "大曲剣の攻撃でＨＰ回復",
    "大曲剣の攻撃力上昇",
    "大曲剣の攻撃力上昇",
    "大曲剣の武器種を３つ以上装備していると攻撃力上昇",
    "大曲剣の武器種を３つ以上装備していると攻撃力上昇",
    "大剣の攻撃でＦＰ回復",
    "大剣の攻撃でＦＰ回復",
    "大剣の攻撃でＨＰ回復",
    "大剣の攻撃でＨＰ回復",
    "大剣の攻撃力上昇",
    "大剣の攻撃力上昇",
    "大剣の武器種を３つ以上装備していると攻撃力上昇",
    "大剣の武器種を３つ以上装備していると攻撃力上昇",
    "大盾の武器種を３つ以上装備していると最大ＨＰ上昇",
    "大盾の武器種を３つ以上装備していると最大ＨＰ上昇",
    "大槍の攻撃でＦＰ回復",
    "大槍の攻撃でＦＰ回復",
    "大槍の攻撃でＨＰ回復",
    "大槍の攻撃でＨＰ回復",
    "大槍の攻撃力上昇",
    "大槍の攻撃力上昇",
    "大槍の武器種を３つ以上装備していると攻撃力上昇",
    "大槍の武器種を３つ以上装備していると攻撃力上昇",
    "大槌の攻撃でＦＰ回復",
    "大槌の攻撃でＦＰ回復",
    "大槌の攻撃でＨＰ回復",
    "大槌の攻撃でＨＰ回復",
    "大槌の攻撃力上昇",
    "大槌の攻撃力上昇",
    "大槌の武器種を３つ以上装備していると攻撃力上昇",
    "大槌の武器種を３つ以上装備していると攻撃力上昇",
    "大斧の攻撃でＦＰ回復",
    "大斧の攻撃でＦＰ回復",
    "大斧の攻撃でＨＰ回復",
    "大斧の攻撃でＨＰ回復",
    "大斧の攻撃力上昇",
    "大斧の攻撃力上昇",
    "大斧の武器種を３つ以上装備していると攻撃力上昇",
    "大斧の武器種を３つ以上装備していると攻撃力上昇",
    "大野営地の強敵を倒す度、最大スタミナ上昇",
    "短剣の攻撃でＦＰ回復",
    "短剣の攻撃でＦＰ回復",
    "短剣の攻撃でＨＰ回復",
    "短剣の攻撃でＨＰ回復",
    "短剣の攻撃力上昇",
    "短剣の攻撃力上昇",
    "短剣の武器種を３つ以上装備していると攻撃力上昇",
    "短剣の武器種を３つ以上装備していると攻撃力上昇",
    "知力＋１",
    "知力＋２",
    "知力＋３",
    "致命の一撃で、アーツゲージ蓄積増加",
    "致命の一撃で、アーツゲージ蓄積増加",
    "致命の一撃で、アーツゲージ蓄積増加＋１",
    "致命の一撃で、スタミナ回復速度上昇",
    "致命の一撃で、スタミナ回復速度上昇",
    "致命の一撃で、スタミナ回復速度上昇＋１",
    "致命の一撃で、ルーンを取得",
    "致命の一撃で、ルーンを取得",
    "致命の一撃強化",
    "致命の一撃強化",
    "致命の一撃強化＋１",
    "中盾の武器種を３つ以上装備していると最大ＨＰ上昇",
    "中盾の武器種を３つ以上装備していると最大ＨＰ上昇",
    "調香術強化",
    "調香術強化",
    "調香術強化＋１",
    "直剣の攻撃でＦＰ回復",
    "直剣の攻撃でＦＰ回復",
    "直剣の攻撃でＨＰ回復",
    "直剣の攻撃でＨＰ回復",
    "直剣の攻撃力上昇",
    "直剣の攻撃力上昇",
    "直剣の武器種を３つ以上装備していると攻撃力上昇",
    "直剣の武器種を３つ以上装備していると攻撃力上昇",
    "槌の攻撃でＦＰ回復",
    "槌の攻撃でＦＰ回復",
    "槌の攻撃でＨＰ回復",
    "槌の攻撃でＨＰ回復",
    "槌の攻撃力上昇",
    "槌の攻撃力上昇",
    "槌の武器種を３つ以上装備していると攻撃力上昇",
    "槌の武器種を３つ以上装備していると攻撃力上昇",
    "通常攻撃の1段目強化",
    "通常攻撃の1段目強化",
    "爪の攻撃でＦＰ回復",
    "爪の攻撃でＦＰ回復",
    "爪の攻撃でＨＰ回復",
    "爪の攻撃でＨＰ回復",
    "爪の攻撃力上昇",
    "爪の攻撃力上昇",
    "爪の武器種を３つ以上装備していると攻撃力上昇",
    "爪の武器種を３つ以上装備していると攻撃力上昇",
    "敵を倒した時、自身を除く周囲の味方のＨＰを回復",
    "敵を倒した時、自身を除く周囲の味方のＨＰを回復",
    "敵を倒した時のアーツゲージ蓄積増加",
    "敵を倒した時のアーツゲージ蓄積増加",
    "敵を倒した時のアーツゲージ蓄積増加＋１",
    "凍傷状態の敵に対する攻撃を強化",
    "凍傷状態の敵に対する攻撃を強化",
    "凍傷状態の敵に対する攻撃を強化＋１",
    "凍傷状態の敵に対する攻撃を強化＋２",
    "刀の攻撃でＦＰ回復",
    "刀の攻撃でＦＰ回復",
    "刀の攻撃でＨＰ回復",
    "刀の攻撃でＨＰ回復",
    "刀の攻撃力上昇",
    "刀の攻撃力上昇",
    "刀の武器種を３つ以上装備していると攻撃力上昇",
    "刀の武器種を３つ以上装備していると攻撃力上昇",
    "投擲ナイフの攻撃力上昇",
    "投擲ナイフの攻撃力上昇",
    "投擲ナイフの攻撃力上昇＋１",
    "投擲壺の攻撃力上昇",
    "投擲壺の攻撃力上昇",
    "投擲壺の攻撃力上昇＋１",
    "特大剣の攻撃でＦＰ回復",
    "特大剣の攻撃でＦＰ回復",
    "特大剣の攻撃でＨＰ回復",
    "特大剣の攻撃でＨＰ回復",
    "特大剣の攻撃力上昇",
    "特大剣の攻撃力上昇",
    "特大剣の武器種を３つ以上装備していると攻撃力上昇",
    "特大剣の武器種を３つ以上装備していると攻撃力上昇",
    "特大武器の攻撃でＦＰ回復",
    "特大武器の攻撃でＦＰ回復",
    "特大武器の攻撃でＨＰ回復",
    "特大武器の攻撃でＨＰ回復",
    "特大武器の攻撃力上昇",
    "特大武器の攻撃力上昇",
    "特大武器の武器種を３つ以上装備していると攻撃力上昇",
    "特大武器の武器種を３つ以上装備していると攻撃力上昇",
    "毒状態の敵に対する攻撃を強化",
    "毒状態の敵に対する攻撃を強化",
    "毒状態の敵に対する攻撃を強化＋１",
    "毒状態の敵に対する攻撃を強化＋２",
    "毒耐性上昇",
    "毒耐性上昇",
    "毒耐性上昇＋１",
    "二刀持ちの、体勢を崩す力上昇",
    "発狂状態になると、ＦＰ持続回復",
    "発狂耐性上昇",
    "発狂耐性上昇",
    "発狂耐性上昇＋１",
    "不可視の魔術を強化",
    "不可視の魔術を強化",
    "斧の攻撃でＦＰ回復",
    "斧の攻撃でＦＰ回復",
    "斧の攻撃でＨＰ回復",
    "斧の攻撃でＨＰ回復",
    "斧の攻撃力上昇",
    "斧の攻撃力上昇",
    "斧の武器種を３つ以上装備していると攻撃力上昇",
    "斧の武器種を３つ以上装備していると攻撃力上昇",
    "斧槍の攻撃でＦＰ回復",
    "斧槍の攻撃でＦＰ回復",
    "斧槍の攻撃でＨＰ回復",
    "斧槍の攻撃でＨＰ回復",
    "斧槍の攻撃力上昇",
    "斧槍の攻撃力上昇",
    "斧槍の武器種を３つ以上装備していると攻撃力上昇",
    "斧槍の武器種を３つ以上装備していると攻撃力上昇",
    "腐敗状態の敵に対する攻撃を強化",
    "腐敗状態の敵に対する攻撃を強化",
    "腐敗状態の敵に対する攻撃を強化＋１",
    "腐敗状態の敵に対する攻撃を強化＋２",
    "腐敗耐性上昇",
    "腐敗耐性上昇",
    "腐敗耐性上昇＋１",
    "武器の持ち替え時、いずれかの属性攻撃力を付加",
    "武器の持ち替え時、物理攻撃力上昇",
    "封牢の囚を倒す度、攻撃力上昇",
    "物理カット率上昇",
    "物理カット率上昇＋１",
    "物理カット率上昇＋２",
    "物理攻撃力上昇",
    "物理攻撃力上昇",
    "物理攻撃力上昇＋１",
    "物理攻撃力上昇＋１",
    "物理攻撃力上昇＋２",
    "物理攻撃力上昇＋２",
    "物理攻撃力上昇＋３",
    "物理攻撃力上昇＋４",
    "鞭の攻撃でＦＰ回復",
    "鞭の攻撃でＦＰ回復",
    "鞭の攻撃でＨＰ回復",
    "鞭の攻撃でＨＰ回復",
    "鞭の攻撃力上昇",
    "鞭の攻撃力上昇",
    "鞭の武器種を３つ以上装備していると攻撃力上昇",
    "鞭の武器種を３つ以上装備していると攻撃力上昇",
    "魔術強化",
    "魔術強化＋１",
    "魔術強化＋２",
    "魔術師塔の仕掛けが解除される度、最大ＦＰ上昇",
    "魔力カット率上昇",
    "魔力カット率上昇",
    "魔力カット率上昇＋１",
    "魔力カット率上昇＋２",
    "魔力攻撃力上昇",
    "魔力攻撃力上昇",
    "魔力攻撃力上昇＋１",
    "魔力攻撃力上昇＋１",
    "魔力攻撃力上昇＋２",
    "魔力攻撃力上昇＋２",
    "魔力攻撃力上昇＋３",
    "魔力攻撃力上昇＋４",
    "埋もれ宝の位置を地図に表示",
    "埋もれ宝の位置を地図に表示",
    "夜の侵入者を倒す度に、攻撃力上昇",
    "雷カット率上昇",
    "雷カット率上昇",
    "雷カット率上昇＋１",
    "雷カット率上昇＋２",
    "雷攻撃力上昇",
    "雷攻撃力上昇",
    "雷攻撃力上昇＋１",
    "雷攻撃力上昇＋１",
    "雷攻撃力上昇＋２",
    "雷攻撃力上昇＋２",
    "雷攻撃力上昇＋３",
    "雷攻撃力上昇＋４",
    "竜餐の祈祷を強化",
    "竜餐の祈祷を強化",
    "両手持ちの、体勢を崩す力上昇",
    "両刃剣の攻撃でＦＰ回復",
    "両刃剣の攻撃でＦＰ回復",
    "両刃剣の攻撃でＨＰ回復",
    "両刃剣の攻撃でＨＰ回復",
    "両刃剣の攻撃力上昇",
    "両刃剣の攻撃力上昇",
    "両刃剣の武器種を３つ以上装備していると攻撃力上昇",
    "両刃剣の武器種を３つ以上装備していると攻撃力上昇",
    "冷気耐性上昇",
    "冷気耐性上昇",
    "冷気耐性上昇＋１",
    "咆哮とブレス強化",
]
DISADVANTAGE_EFFECTS = [
    "生命力と神秘が低下",
    "筋力と知力が低下",
    "技量と信仰が低下",
    "知力と技量が低下",
    "信仰と筋力が低下",
    "取得ルーン減少",
    "ＨＰ持続減少",
    "すべての状態異常耐性低下",
    "聖杯瓶使用時、カット率低下",
    "回避直後の被ダメージ増加",
    "回避連続時、カット率低下",
    "被ダメージ時、毒を蓄積",
    "被ダメージ時、腐敗を蓄積",
    "被ダメージ時、出血を蓄積",
    "被ダメージ時、冷気を蓄積",
    "被ダメージ時、睡眠を蓄積",
    "被ダメージ時、発狂を蓄積",
    "被ダメージ時、死を蓄積",
    "聖杯瓶の回復量低下",
    "アーツゲージ蓄積鈍化",
    "ＨＰ最大未満時、攻撃力低下",
    "ＨＰ最大未満時、毒が蓄積",
    "ＨＰ最大未満時、腐敗が蓄積",
    "瀕死時、最大ＨＰ低下",
]
HAS_DISADVANTEGE_EFFECT_NAMES = [
    "最大ＨＰ上昇",
    "最大ＦＰ上昇",
    "最大スタミナ上昇",
    "物理攻撃力上昇＋３",
    "物理攻撃力上昇＋４",
    "属性攻撃力上昇＋１",
    "属性攻撃力上昇＋２",
    "魔力攻撃力上昇＋３",
    "魔力攻撃力上昇＋４",
    "炎攻撃力上昇＋３",
    "炎攻撃力上昇＋４",
    "雷攻撃力上昇＋３",
    "雷攻撃力上昇＋４",
    "聖攻撃力上昇＋３",
    "聖攻撃力上昇＋４",
    "魔術強化＋１",
    "魔術強化＋２",
    "祈祷強化＋１",
    "祈祷強化＋２",
    "ガードカウンター強化＋１",
    "ガードカウンター強化＋２",
    "脂アイテム使用時、追加で物理攻撃力上昇＋１",
    "脂アイテム使用時、追加で物理攻撃力上昇＋２",
    "敵を倒した時のアーツゲージ蓄積増加＋１",
    "致命の一撃で、アーツゲージ蓄積増加＋１",
    "ガード成功時、アーツゲージを蓄積＋１",
    "物理カット率上昇＋１",
    "物理カット率上昇＋２",
    "属性カット率上昇＋１",
    "属性カット率上昇＋２",
    "魔力カット率上昇＋１",
    "魔力カット率上昇＋２",
    "炎カット率上昇＋１",
    "炎カット率上昇＋２",
    "雷カット率上昇＋１",
    "雷カット率上昇＋２",
    "聖カット率上昇＋１",
    "聖カット率上昇＋２",
    "刺突カウンター発生時、ＨＰ回復＋１",
    "ダメージを受けた直後、攻撃によりＨＰの一部を回復＋１",
    "ダメージを受けた直後、攻撃によりＨＰの一部を回復＋２",
    "毒状態の敵に対する攻撃を強化＋１",
    "毒状態の敵に対する攻撃を強化＋２",
    "腐敗状態の敵に対する攻撃を強化＋１",
    "腐敗状態の敵に対する攻撃を強化＋２",
    "凍傷状態の敵に対する攻撃を強化＋１",
    "凍傷状態の敵に対する攻撃を強化＋２",
    "周囲で睡眠状態の発生時、攻撃力上昇＋１",
    "周囲で発狂状態の発生時、攻撃力上昇＋１",
]
RELIC_INFO_DICT = {
    "ちぎれた組み紐": {"color": "blue", "type": "normal"},
    "にび色の砥石": {"color": "red", "type": "normal"},
    "王の夜": {"color": "blue", "type": "normal"},
    "黄金の萌芽": {"color": "red", "type": "normal"},
    "霞の暗き夜": {"color": "green", "type": "normal"},
    "霞の夜": {"color": "yellow", "type": "normal"},
    "割れた封蝋": {"color": "yellow", "type": "normal"},
    "忌み鬼の呪物": {"color": "blue", "type": "normal"},
    "金色の露": {"color": "yellow", "type": "normal"},
    "銀の雫": {"color": "red", "type": "normal"},
    "古びたミニアチュール": {"color": "blue", "type": "normal"},
    "古びた懐中時計": {"color": "green", "type": "normal"},
    "黒爪の首飾り": {"color": "yellow", "type": "normal"},
    "骨のような石": {"color": "green", "type": "normal"},
    "砕けた魔女のブローチ": {"color": "blue", "type": "normal"},
    "三冊目の本": {"color": "red", "type": "normal"},
    "識の暗き夜": {"color": "green", "type": "normal"},
    "識の夜": {"color": "yellow", "type": "normal"},
    "爵の暗き夜": {"color": "red", "type": "normal"},
    "爵の夜": {"color": "blue", "type": "normal"},
    "狩人の暗き夜": {"color": "yellow", "type": "normal"},
    "狩人の夜": {"color": "green", "type": "normal"},
    "獣の暗き夜": {"color": "yellow", "type": "normal"},
    "獣の夜": {"color": "green", "type": "normal"},
    "祝福された花": {"color": "green", "type": "normal"},
    "祝福された鉄貨": {"color": "green", "type": "normal"},
    "小さな化粧道具": {"color": "blue", "type": "normal"},
    "深海の暗き夜": {"color": "blue", "type": "normal"},
    "深海の夜": {"color": "red", "type": "normal"},
    "聖律の刃": {"color": "yellow", "type": "normal"},
    "石の杭": {"color": "red", "type": "normal"},
    "繊細な輝く景色": {"color": "yellow", "type": "normal"},
    "繊細な輝く昏景": {"color": "yellow", "type": "depth"},
    "繊細な静まる景色": {"color": "green", "type": "normal"},
    "繊細な静まる昏景": {"color": "green", "type": "depth"},
    "繊細な滴る景色": {"color": "blue", "type": "normal"},
    "繊細な滴る昏景": {"color": "blue", "type": "depth"},
    "繊細な燃える景色": {"color": "red", "type": "normal"},
    "繊細な燃える昏景": {"color": "red", "type": "depth"},
    "壮大な輝く景色": {"color": "yellow", "type": "normal"},
    "壮大な輝く昏景": {"color": "yellow", "type": "depth"},
    "壮大な静まる景色": {"color": "green", "type": "normal"},
    "壮大な静まる昏景": {"color": "green", "type": "depth"},
    "壮大な滴る景色": {"color": "blue", "type": "normal"},
    "壮大な滴る昏景": {"color": "blue", "type": "depth"},
    "壮大な燃える景色": {"color": "red", "type": "normal"},
    "壮大な燃える昏景": {"color": "red", "type": "depth"},
    "端正な輝く景色": {"color": "yellow", "type": "normal"},
    "端正な輝く昏景": {"color": "yellow", "type": "depth"},
    "端正な静まる景色": {"color": "green", "type": "normal"},
    "端正な静まる昏景": {"color": "green", "type": "depth"},
    "端正な滴る景色": {"color": "blue", "type": "normal"},
    "端正な滴る昏景": {"color": "blue", "type": "depth"},
    "端正な燃える景色": {"color": "red", "type": "normal"},
    "端正な燃える昏景": {"color": "red", "type": "depth"},
    "追跡者の耳飾り": {"color": "red", "type": "normal"},
    "頭冠のメダル": {"color": "green", "type": "normal"},
    "薄汚れたフレーム": {"color": "blue", "type": "normal"},
    "魔の暗き夜": {"color": "blue", "type": "normal"},
    "魔の夜": {"color": "red", "type": "normal"},
    "魔女のブローチ": {"color": "blue", "type": "normal"},
    "夜の痕跡": {"color": "green", "type": "normal"},
}
IGNORE_FULLSCORE_CHARS = [
    "、",
    "（",
    "）",
    "※",
    "べ",
    "演",
    "音",
    "換",
    "近",
    "再",
    "事",
    "衝",
    "全",
    "足",
    "適",
    "難",
    "能",
    "波",
    "避",
    "瀕",
    "来",
]

# === ROI 比率変換 ===
def scaled_rect(x1, y1, x2, y2, fw, fh):
    sx = math.floor(fw * x1 / CALC_BASE_WIDTH)
    sy = math.floor(fh * y1 / CALC_BASE_HEIGHT)
    ex = math.ceil(fw * x2 / CALC_BASE_WIDTH)
    ey = math.ceil(fh * y2 / CALC_BASE_HEIGHT)
    return {"x1": sx, "y1": sy, "x2": ex, "y2": ey}

# === ROI内の平均差分を返す ===
def calc_region_diff(prev_gray, gray, rect):
    x1, y1, x2, y2 = rect["x1"], rect["y1"], rect["x2"], rect["y2"]
    region_prev = prev_gray[y1:y2, x1:x2]
    region_curr = gray[y1:y2, x1:x2]
    diff = cv2.absdiff(region_prev, region_curr)
    return np.mean(diff)

# === 前処理 ===
def preprocess(img):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if len(img.shape) == 3 else img
    return cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)[1]


# === 類似度計算 ===
def calc_similarity(img_gray, template_gray):
    try:
        res = cv2.matchTemplate(img_gray, template_gray, cv2.TM_CCOEFF_NORMED)
        return float(np.max(res))
    except:
        return 0.0


# === 最も近い文字を推定 ===
def match_best_char(char_img_gray, labeled_dict, score_th=0.5):
    best_char, best_score = None, 0.0
    for ch, samples in labeled_dict.items():
        ch = ch.replace("\r", "")
        for tmpl in samples:
            score = calc_similarity(char_img_gray, tmpl)
            if score < score_th:
                continue

            if score == 1.0:
                if ch in IGNORE_FULLSCORE_CHARS:
                    continue  # 誤認識対策

            if score > best_score:
                best_score = score
                best_char = ch
    return best_char, best_score


# === labeled_chars 読み込み ===
def load_labeled_templates(average=True):
    templates = {"name": {}, "effect": {}}
    for kind, base_dir in [("name", NAME_DIR), ("effect", EFFECT_DIR)]:
        if not os.path.isdir(base_dir):
            continue
        grouped = {}
        for fname in os.listdir(base_dir):
            if not fname.endswith(".png"):
                continue
            label = os.path.splitext(fname)[0]
            label = label[0] if kind == "effect" else label
            label = unicodedata.normalize("NFC", label)
            path = os.path.join(base_dir, fname)
            img = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
            if img is None:
                continue
            img_proc = preprocess(img)
            grouped.setdefault(label, []).append(img_proc)

        # --- 平均化 ---
        for label, imgs in grouped.items():
            if average:
                # サイズを揃える（最小サイズ基準）
                h_min = min(i.shape[0] for i in imgs)
                w_min = min(i.shape[1] for i in imgs)
                resized = [cv2.resize(i, (w_min, h_min)) for i in imgs]
                avg = np.mean(resized, axis=0).astype(np.uint8)
                templates[kind][label] = [avg]
            else:
                templates[kind][label] = imgs

    return templates


# === 1行テキストを認識 ===
def recognize_text(line_img, labeled_dict, char_width, n_chars=40):
    gray = preprocess(line_img)
    h, w = gray.shape
    result = ""
    for i in range(n_chars):
        x1 = i * char_width
        x2 = min((i + 1) * char_width, w)
        char_img = gray[:, x1:x2]
        ch, score = match_best_char(char_img, labeled_dict)
        if ch is None or (result and result[-1] == ch):
            break
        result += ch if ch else ""
    return unicodedata.normalize("NFC", result.strip())


# === 効果文の照合 ===
def find_closest_effect(text, effect_list):
    text = text.replace("※適用可能な武器種のみ", "").strip()
    if not text:
        return ""
    matches = difflib.get_close_matches(text, effect_list, n=1, cutoff=0.5)
    return matches[0] if matches else ""


# === CSV 出力 ===
def save_csv(rows, path):
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["No.", "Name", "Color", "Effect1", "Effect2", "Effect3", "Disadvantage1", "Disadvantage2", "Disadvantage3"])
        writer.writerows(rows)


# === ROI 切り出し（デバッグ出力付き） ===
def crop_region(gray, rect, label):
    y1, y2, x1, x2 = rect["y1"], rect["y2"], rect["x1"], rect["x2"]
    if y2 <= y1 or x2 <= x1:
        print(f"⚠️ ROI invalid for {label}")
        return np.zeros((1, 1), dtype=np.uint8)
    return gray[y1:y2, x1:x2]


# === 動画解析 ===
def analyze_relics(cap, frame, templates):

    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    print("Total frame:", total_frames)
    FRAME_HEIGHT, FRAME_WIDTH = frame.shape[:2]
    print("Detected frame size:", FRAME_WIDTH, FRAME_HEIGHT)
    name_char_width = int(CALC_BASE_RELIC_NAME_CHAR_WIDTH * FRAME_WIDTH / CALC_BASE_WIDTH)
    effect_char_width = int(CALC_BASE_RELIC_EFFECT_CHAR_WIDTH * FRAME_WIDTH / CALC_BASE_WIDTH)

    # ROI 定義（動画サイズに合わせて変換）
    ROIS = {
        "name": scaled_rect(2150, 1550, 2900, 1600, FRAME_WIDTH, FRAME_HEIGHT),
        "effect1_1": scaled_rect(2220, 1630, 3820, 1670, FRAME_WIDTH, FRAME_HEIGHT),
        "effect1_2": scaled_rect(2220, 1678, 3820, 1720, FRAME_WIDTH, FRAME_HEIGHT),
        "effect2_1": scaled_rect(2220, 1750, 3820, 1790, FRAME_WIDTH, FRAME_HEIGHT),
        "effect2_2": scaled_rect(2220, 1798, 3820, 1840, FRAME_WIDTH, FRAME_HEIGHT),
        "effect3_1": scaled_rect(2220, 1870, 3820, 1910, FRAME_WIDTH, FRAME_HEIGHT),
        "effect3_2": scaled_rect(2220, 1918, 3820, 1960, FRAME_WIDTH, FRAME_HEIGHT),
    }
    DIFF_REGION = scaled_rect(1855, 1487, 3820, 1960, FRAME_WIDTH, FRAME_HEIGHT)

    rows = []
    last_name = last_effects = prev_gray = None

    try:
        frame_idx = 0
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            frame_idx += 1

            progress = math.floor(frame_idx / total_frames * 100 * 10) / 10
            print(f"Frame {frame_idx}/{total_frames} ({progress:.1f}%)", end='\r')

            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            # === 差分チェック ===
            if prev_gray is not None:
                diff_value = calc_region_diff(prev_gray, gray, DIFF_REGION)
                if diff_value <= FRAME_SKIP_DIFF_TH:
                    continue
            prev_gray = gray.copy()

            # === 名前 ===
            name_img = crop_region(gray, ROIS["name"], "name")
            name_text = recognize_text(name_img, templates["name"], name_char_width * RELIC_NAME_CHARS, 1)
            relic_info = RELIC_INFO_DICT[name_text]
            has_disadvantages = relic_info["type"] == "depth"

            # === 効果 ===
            effects = []
            disadvantages = []
            for i in range(1, 4):
                line1 = crop_region(gray, ROIS[f"effect{i}_1"], f"effect{i}_1")
                line2 = crop_region(gray, ROIS[f"effect{i}_2"], f"effect{i}_2")

                line1_text = recognize_text(line1, templates["effect"], effect_char_width, RELIC_EFFECT_CHARS)
                line2_text = recognize_text(line2, templates["effect"], effect_char_width, RELIC_EFFECT_CHARS)

                if "|" in line1_text or  "｜" in line1_text:
                    # 1行に効果とデメリットが混在している場合
                    part1, part2 = re.split(r'[|｜]', line1_text, 1)
                    matched_effect = find_closest_effect(part1.strip(), EFFECT_LIST)
                    matched_disadvantage = find_closest_effect(part2.strip(), DISADVANTAGE_EFFECTS) if has_disadvantages else ""
                else:
                    # 2行に分かれている or パイプ(|)が認識できなかった場合
                    matched_effect = find_closest_effect(line1_text, EFFECT_LIST)
                    matched_disadvantage = find_closest_effect(line2_text, DISADVANTAGE_EFFECTS) if has_disadvantages else ""
                    if not matched_effect and not matched_disadvantage:
                        # 2行に分かれている想定でテキストを結合して処理
                        combined = line1_text + line2_text
                        matched_effect = find_closest_effect(combined, EFFECT_LIST)
                        matched_disadvantage = find_closest_effect(combined, DISADVANTAGE_EFFECTS) if has_disadvantages else ""
                    elif matched_effect and not matched_disadvantage and has_disadvantages:
                        # 効果は見つかったけどデメリットが見つからない場合、1行目にまとまっている想定でチェック
                        matched_disadvantage = find_closest_effect(line1_text, DISADVANTAGE_EFFECTS)

                if matched_effect not in HAS_DISADVANTEGE_EFFECT_NAMES:
                    matched_disadvantage = "";
                elif matched_disadvantage == "":
                    print(f"Frame {frame_idx}: Effect {i}: {matched_effect}: Disadvantage analyze error!!")

                effects.append(matched_effect)
                disadvantages.append(matched_disadvantage)

            # === 前フレームと重複チェック ===
            print(f"Frame {frame_idx}: Name='{name_text}', Effects={effects}, Disadvantages={disadvantages}")
            if name_text == last_name and effects == last_effects:
                continue

            rows.append([len(rows) + 1, name_text, relic_info["color"]] + effects + disadvantages)
            last_name, last_effects = name_text, effects

    except KeyboardInterrupt:
        print("Interrupted by user.")

    return rows


# === メイン処理 ===
def main():
    print("遺物儀式画面の動画から遺物一覧CSVを作成します。100%の精度ではないため抽出漏れや解析誤りなどの可能性があります。")

    # labeled_chars 読み込み
    templates = load_labeled_templates()

    # 動画読み込み
    cap = cv2.VideoCapture(VIDEO_PATH)
    ret, frame = cap.read()
    if not ret:
        print("動画が読み込めません。実行ファイルと同じフォルダ(ディレクトリ)に relics.mp4 を配置してください。")
        return

    rows = analyze_relics(cap, frame, templates)
    cap.release()
    save_csv(rows, CSV_PATH)
    print(f"✅ CSV saved: {CSV_PATH} ({len(rows)} rows)")


if __name__ == "__main__":
    main()
