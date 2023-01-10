# You'd need the zulip command line client installed via `pip install zulip`
# and credentials for an account in `$TMP_DIR/zuliprc`.

TARGETS="algebra.order.floor data.real.basic linear_algebra.basic data.fintype.basic algebra.big_operators.basic order.filter.basic category_theory.limits.yoneda data.complex.basic topology.metric_space.basic all"
BASE_URL=https://math.commelin.net/files/mathlib4
TMP_DIR=/home/jmc/data/math/port_progress
GRAPH_DIR=/home/jmc/sites/math/files/mathlib4

mkdir -p $TMP_DIR
today=$(date -I)
mkdir -p $GRAPH_DIR/$today/

cd $TMP_DIR
cd mathlib
git clean -xfd
git pull
leanpkg configure
leanproject get-cache
scripts/mk_all.sh

cd $GRAPH_DIR
ln -sfn $today latest

cd $TMP_DIR/mathlib
for target in $TARGETS; do

    leanproject port-progress --to $target > $target.out
    cat $target.out | tail -n +6 > $GRAPH_DIR/$today/$target
    cat $target.out | \
      head -n 5 | \
      sed -e "s%\(mathlib port progress *| \)\([0-9a-z_\.]*\)%\1[\2]($BASE_URL/$today/\2.pdf)%" | \
      sed -e "s|\(Longest unported chain\)|[\1]($BASE_URL/$today/$target)|" | \
      zulip-send -s mathlib4 --subject "port progress" --config-file $TMP_DIR/zuliprc

done
