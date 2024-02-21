import json
import logging
from functools import cache
from enum import Enum, auto
from pypinyin import pinyin, Style
from tqdm import tqdm

logging.basicConfig(
    format="[%(levelname)s] %(lineno)d : %(msg)s",
    level=logging.DEBUG,
)
debug = logging.debug
info = logging.info


def flattened_pinyin(*args, **kwargs):
    res = pinyin(*args, **kwargs)
    return [i[0] for i in res]


@cache
def get_info(s):
    pinyin = flattened_pinyin
    chars = list(s)
    initials = pinyin(s, style=Style.INITIALS, strict=False)
    final_tones = pinyin(s, style=Style.FINALS_TONE3)
    tones = [
        i[-1:] if i[-1:].isdigit() else ""
        for i in final_tones
    ]
    finals = [
        i[:-1] if i[-1:].isdigit() else i
        for i in final_tones
    ]
    return initials, finals, tones, chars


class GuessType(Enum):
    A = auto()  # is not in the word in any spot.
    B = auto()  # is in the word but in the wrong spot.
    C = auto()  # is in the word and in the correct spot.


class GuessMatrix:
    def check(self, guess: list, answer: list):
        result = []
        for i in range(len(guess)):
            if guess[i] == answer[i]:
                result.append(GuessType.C)
            elif guess[i] in answer:
                result.append(GuessType.B)
            else:
                result.append(GuessType.A)
        return result

    @classmethod
    def register_idioms(cls, idioms: dict):
        cls.idioms = idioms

    def get_info(self, s):
        res = self.idioms.get(s)
        if res:
            return res.values()
        res = get_info(s)
        return res

    def __init__(self, guess: str, answer: str = "", matrix=None):
        if not answer and not matrix:
            raise ValueError("answer or matrix is required")
        if answer and matrix:
            raise ValueError("only one is required, but both two are given")
        if matrix:
            self.matrix = matrix
        else:
            guess = self.get_info(guess)
            answer = self.get_info(answer)
            self.matrix = []
            for i, j in zip(guess, answer):
                self.matrix.append(self.check(i, j))

    def __str__(self):
        return str(self.matrix)

    __repr__ = __str__

    def __eq__(self, other):
        for i in range(len(self.matrix)):
            for j in range(len(self.matrix[i])):
                if self.matrix[i][j] != other.matrix[i][j]:
                    return False
        return True


def calc_all():
    guess_scores = []
    cnt = 0
    for guess in all_idioms:
        info(guess)
        counters = []
        for answer in tqdm(all_idioms):
            matrix = GuessMatrix(guess, answer)
            counter = 0
            for i in all_idioms:
                matrix2 = GuessMatrix(guess, i)
                if matrix != matrix2:
                    counter += 1
            counters.append(counter)
        avg_counter = sum(counters) / len(counters)
        guess_scores.append((guess, avg_counter))
        cnt += 1
        if cnt >= 20:
            break
    print(guess_scores)


def filter(idioms, guesses, mats):
    result = []
    for i in idioms.keys():
        if all(
                GuessMatrix(guess, i) == mat
                for guess, mat in zip(guesses, mats)
                ):
            result.append(i)
    return result


if __name__ == "__main__":
    with open("idioms2.json", 'r', encoding="utf-8") as f:
        idioms = {k: v for k, v in json.load(f).items() if len(k) == 4}
    GuessMatrix.register_idioms(idioms)

    guesses = []
    mats = []
    while True:
        s = input("你的猜测：\n")
        assert len(s) == 4
        matrix = []
        alpha2type = {
            "A": GuessType.A,
            "B": GuessType.B,
            "C": GuessType.C,
        }
        for item in "声母 韵母 声调 汉字".split():
            row = input(f"{item}猜测结果（A=没有；B=有，位置错；C=有，位置对）：\n")
            assert len(row) == 4
            matrix.append([alpha2type[a] for a in row])

        guesses.append(s)
        mats.append(GuessMatrix("", matrix=matrix))
        res = filter(idioms, guesses, mats)
        print(res)
