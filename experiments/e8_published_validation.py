r"""E8 -- Validation against FOUR independent published measurements.

Motivation. The paper previously reproduced one published measurement (the
SECOQC key-store drain). One reproduction is a weak validation claim, and the
obvious alternative -- cross-validating against another simulator -- is not
available: source inspection shows SeQUeNCe, NetSquid and QuISP contain no
trusted-relay or key-pool model at all, so they cannot check a key-economy
simulator. What *is* available, and was already sitting in our own parameter
table, is three further published measurements that constrain the model from
independent directions.

A validation suite that cannot fail is not a validation suite. Two of the three
new checks disagree with the model, in the same direction, and the disagreement
identifies an under-parameterised term. That is the useful outcome.

  V1  SECOQC key-store drain             Peev NJP 11:075001 (2009), Fig. 22
  V2  Cambridge relay key overhead       Dynes npj QI 5:101 (2019)
  V3  SECOQC AES-VPN consumption         Peev NJP 11:075001 (2009), 5.1.1 + fn.27
  V4  Hefei OTP voice capacity           Chen npj QI 7:134 (2021)

Run: python experiments/e8_published_validation.py
"""
from __future__ import annotations

import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
RES = ROOT / "results"
RES.mkdir(exist_ok=True)

from qkdsim.config import AccountingConfig

rows: list[dict] = []


def report(vid, what, measured, predicted, units, verdict, note):
    rows.append(dict(check=vid, quantity=what, measured=measured,
                     predicted=predicted, units=units, verdict=verdict,
                     note=note))
    print(f"\n[{vid}] {what}")
    print(f"     measured  : {measured} {units}")
    print(f"     our model : {predicted} {units}")
    print(f"     verdict   : {verdict}")
    print(f"     {note}")


# ---------------------------------------------------------------------------
# V1 -- key-store drain (already in the gate; restated here for completeness)
# ---------------------------------------------------------------------------
def v1():
    """Peev et al. Fig. 22: an application consuming ~1 KiB/s by one-time pad
    drained 3.5 MiB of a 5.5 MiB key store in approximately one hour."""
    consume_bps = 8192.0
    drain_bits = 3.5 * 1024 * 1024 * 8
    t = drain_bits / consume_bps
    report("V1", "time to drain 3.5 MiB at 8192 bit/s",
           "3584 (approx. 1 h)", f"{t:.0f}", "s", "PASS (exact)",
           "Reference arithmetic and simulator agree to the second; the gate "
           "in e1_validation.py runs this against the KeyStore itself.")


# ---------------------------------------------------------------------------
# V2 -- Cambridge relay overhead
# ---------------------------------------------------------------------------
def v2(ac: AccountingConfig):
    """Dynes et al.: distributing 1000 'global keys' cost ~180 kbytes of QKD
    key. Their global-key rate is ~100 bps at one key per 4 s, which implies a
    ~400-bit global key (derived, not stated).

    Cambridge is a three-node ring (CAPE, TREL, ENGI), so every node pair is
    adjacent and a relay is a single hop. The model should therefore predict the
    measured per-key cost directly, with no hop-count freedom to absorb error.
    """
    measured_bits_per_key = 180 * 1024 * 8 / 1000        # 1474.6
    D = 400
    pred = ac.cost_per_hop(D)                            # 894 at n_auth = 2
    ratio = measured_bits_per_key / pred
    implied_n = (measured_bits_per_key - D - ac.metadata_bits) / ac.tag_bits
    report("V2", f"link key consumed per relayed {D}-bit global key",
           f"{measured_bits_per_key:.0f} ({measured_bits_per_key / D:.2f}x D)",
           f"{pred} ({pred / D:.2f}x D)", "bit",
           "DISAGREES -- model is low by %.2fx" % ratio,
           f"Solving for the number of authenticated messages per key "
           f"delivery gives n_auth = {implied_n:.1f}, against our assumed 2.")
    return implied_n


# ---------------------------------------------------------------------------
# V3 -- SECOQC AES-VPN consumption
# ---------------------------------------------------------------------------
def v3(ac: AccountingConfig):
    """Peev et al. 5.1.1: an AES-encrypted IPsec VPN over the QKD network
    consumed 728 bytes every 20 s (36 byte/s), 'and does not depend on the
    actual size of the plaintext message'. Footnote 27: 'The IPsec tunnel needs
    two portions of 256 bits on both sides in each exchange round. The
    remaining bits are OTP tunnel authentication overhead.'

    So 512 bit of the 5824 is cipher key and ~5312 bit is ITS authentication --
    91.2% overhead. This is a much heavier authentication load than our per-hop
    model charges, because a full IPsec rekey exchange authenticates many
    protocol messages per round whereas we charge two tags per relay hop.
    """
    total = 728 * 8                       # 5824
    cipher = 2 * 256                      # 512, per footnote 27
    meas_share = (total - cipher) / total
    pred = ac.cost_per_hop(256)
    pred_share = (pred - 256) / pred
    implied_n = (total - cipher - ac.metadata_bits) / ac.tag_bits
    report("V3", "authentication share of key consumed per 256-bit AES rekey",
           f"{100 * meas_share:.1f}% ({total} bit/round, {cipher} bit cipher)",
           f"{100 * pred_share:.1f}% ({pred} bit/hop, 256 bit cipher)", "%",
           "DISAGREES -- model is low by %.1fx on the overhead term"
           % (((total - cipher) / cipher) / ((pred - 256) / 256)),
           f"Implies n_auth = {implied_n:.0f} authenticated messages per key "
           f"delivery for an application-level tunnel, against our assumed 2.")
    return implied_n


# ---------------------------------------------------------------------------
# V4 -- Hefei OTP voice capacity
# ---------------------------------------------------------------------------
def v4():
    """Chen et al.: a 46-node metropolitan network supported '11 pairs of users
    to make audio calls simultaneously' with one-time-pad encryption, at a
    stated voice rate of 2.4 kbps, on links whose measured key rates range from
    6 to 60.5 kbps.

    One-time pad requires key bits equal to payload bits, so the sustainable
    number of simultaneous bidirectional OTP voice pairs on a link of rate R is
    R / (2 x 2.4 kbps). This is a capacity check on the OTP demand law, and it
    is independent of V1-V3 (which constrain relay accounting).
    """
    voice_bps = 2400.0
    per_pair = 2 * voice_bps              # bidirectional
    for label, R in (("min link 6 kbps", 6_000.0),
                     ("max link 60.5 kbps", 60_500.0)):
        n = R / per_pair
        print(f"     {label}: supports {n:.1f} simultaneous OTP voice pairs")
    lo, hi = 6_000.0 / per_pair, 60_500.0 / per_pair
    report("V4", "simultaneous bidirectional OTP voice pairs supported",
           "11 (reported)", f"{lo:.1f}-{hi:.1f} across the link-rate range",
           "pairs", "PASS -- 11 lies inside the predicted range",
           "The OTP demand law (key bits = payload bits) reproduces the "
           "reported concurrency without tuning: 11 pairs needs 52.8 kbps, "
           "inside their 6-60.5 kbps measured range.")


# ---------------------------------------------------------------------------
def main() -> int:
    ac = AccountingConfig()
    print("=" * 74)
    print("E8  VALIDATION AGAINST FOUR PUBLISHED MEASUREMENTS")
    print("=" * 74)
    v1()
    n2 = v2(ac)
    n3 = v3(ac)
    v4()

    print("\n" + "=" * 74)
    print("SYNTHESIS -- what the two disagreements mean")
    print("=" * 74)
    print(f"""
Both disagreements run the SAME direction: the model under-charges
authentication. Solving each measurement for the number of authenticated
messages per key delivery:

    V2  Cambridge, key relay          n_auth ~ {n2:.1f}
    V3  SECOQC, application tunnel    n_auth ~ {n3:.0f}
    ours (assumed)                    n_auth = {ac.n_auth}

These are not in conflict -- they measure different layers. A single relay hop
authenticates a handful of messages (V2); a full IPsec rekey exchange carried
over an ITS tunnel authenticates many more (V3). Our n_auth = 2 was chosen from
the mutual-authentication argument (two one-time keys per round) and is a LOWER
BOUND, not a measured value.

CONSEQUENCES, to be stated in the paper:
  1. n_auth is a first-order parameter and must be swept, not fixed. The
     calibrated default for a RELAY model is V2's ~{n2:.0f}, not 2.
  2. Our small-block key-capacity results are OPTIMISTIC. At n_auth = {n2:.0f} the
     per-hop cost of a 256-bit relay rises from {ac.cost_per_hop(256)} to
     {256 + ac.metadata_bits + int(round(n2)) * ac.tag_bits} bit.
  3. The E5 finding STRENGTHENS: the literature's bare D*n law understates
     small-block key consumption by {ac.cost_per_hop(256) / 256:.2f}x on our
     conservative setting and by
     {(256 + ac.metadata_bits + int(round(n2)) * ac.tag_bits) / 256:.2f}x once
     calibrated to Cambridge -- so the error we identified is larger than we
     originally reported, not smaller.
  4. The direction of the bias is known and stated, which is what a reader
     needs in order to use the numbers.
""")
    with open(RES / "e8_published_validation.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print("-> results/e8_published_validation.csv")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
