from projectdash import model as M
from projectdash.lines import analyse, detect_reorders, progress, set_status


def line(num, article, qty, delivered, remark="", vendor="V", **kw):
    return M.Line(excel_row=int(num) + 4, num=str(num), article=str(article),
                  description=kw.pop("description", f"ITEM {article}"), qty=qty,
                  delivered=delivered, remark=remark, vendor=vendor, **kw)


def run(lines):
    detect_reorders(lines)
    for ln in lines:
        set_status(ln)
    return lines


def test_reorder_with_nothing_delivered_is_excluded():
    a, b = run([line(1, "A", 20, 0, "Out of Stock"), line(2, "A", 20, 20, "Delivered")])
    assert (a.status, a.reordered_as, a.active) == (M.L_REORDERED, "2", False)
    assert (b.status, b.reorder_of) == (M.L_DELIVERED, "1")


def test_reorder_of_the_undelivered_balance_keeps_the_delivered_part():
    a, b = run([line(1, "A", 10, 3, "3 ea Delivered"), line(2, "A", 7, 7)])
    assert a.effective_qty == 3 and a.status == M.L_DELIVERED and a.active
    assert b.status == M.L_DELIVERED


def test_no_reorder_when_quantity_differs_or_line_comes_earlier():
    lines = run([line(1, "A", 5, 5), line(2, "A", 20, 0, "Out of stock"), line(3, "A", 19, 19)])
    assert [ln.reordered_as for ln in lines] == ["", "", ""]
    assert lines[1].status == M.L_OUT_OF_STOCK


def test_a_reorder_that_is_itself_reordered_forms_a_chain_and_counts_once():
    lines = run([line(1, "A", 5, 0), line(2, "A", 5, 0), line(3, "A", 5, 5)])
    assert [ln.reordered_as for ln in lines] == ["2", "3", ""]
    assert [ln.status for ln in lines] == [M.L_REORDERED, M.L_REORDERED, M.L_DELIVERED]
    assert sum(ln.active for ln in lines) == 1


def test_remarks_win_over_quantities():
    assert run([line(1, "A", 5, 5, "pending")])[0].status == M.L_PENDING
    assert run([line(1, "A", 5, 5, "Out of Stock")])[0].status == M.L_OUT_OF_STOCK
    assert run([line(1, "A", 5, 2, "delivered")])[0].status == M.L_PARTIAL
    assert run([line(1, "A", 5, None, "Delivered")])[0].status == M.L_DELIVERED
    assert run([line(1, "A", 5, 0, "Cancelled by client")])[0].status == M.L_CANCELLED


def test_blank_remark_uses_quantities():
    assert run([line(1, "A", 5, 5)])[0].status == M.L_DELIVERED
    assert run([line(1, "A", 5, 2)])[0].status == M.L_PARTIAL
    assert run([line(1, "A", 5, 0)])[0].status == M.L_PENDING
    assert run([line(1, "A", 5, None)])[0].status == M.L_PENDING


def test_conflict_pending_but_fully_delivered_counts_as_not_delivered():
    ln = run([line(1, "A", 15, 15, "pending")])[0]
    assert ln.conflict and ln.status == M.L_PENDING and ln.open
    assert not run([line(1, "A", 15, 0, "pending")])[0].conflict


def test_progress_by_lines_quantity_and_value():
    lines = run([line(1, "A", 100, 100, value=200000.0), line(2, "B", 50, 20, value=200000.0),
                 line(3, "C", 10, 0, "pending", value=380000.0),
                 line(4, "D", 5, 0, "Out of stock"), line(5, "D", 5, 5, value=0.0)])
    lines[3].value = None                                     # excluded re-order has no value
    p = progress(lines)
    assert (p.active_lines, p.delivered_lines) == (4, 2)
    assert p.by_lines == 50.0
    assert p.by_qty == round(100 * (100 + 20 + 5) / 165, 1)
    assert p.basis == "value" and p.by_value == round(100 * 280000 / 780000, 1)


def test_progress_falls_back_to_line_count_when_a_value_is_missing():
    p = progress(run([line(1, "A", 1, 1, value=10.0), line(2, "B", 1, 0)]))
    assert p.basis == "line count" and p.percent == 50.0 and p.by_value is None


def test_conflict_lines_count_zero_in_quantity_progress():
    p = progress(run([line(1, "A", 10, 10, "pending"), line(2, "B", 10, 10)]))
    assert p.by_qty == 50.0 and p.by_lines == 50.0


def test_findings():
    d = M.DetailFile(path="x", name="x.xlsx", lines=[
        line(1, "A", 5, 5, "Delivered", notes="NEED TO MAKE GI", description="FAN SMALL"),
        line(2, "A", 5, 5, "pending", description="FAN LARGE"),
        line(3, "B", 2, 0, "Out of stock", notes="NEED TO REVERSE GI"),
        line(4, "B", 2, 2, "pending", vendor=""),
    ])
    analyse(d)
    assert d.reorders == [("3", "4")]
    assert d.conflict_lines == ["2", "4"]
    assert (d.gi_to_make, d.gi_to_reverse) == (1, 1)
    assert d.reused_articles == ["A"]
    assert {f.code for f in d.flags} == {"line_conflict", "reorders", "gi_notes", "no_vendor",
                                         "article_reuse", "no_values"}
    assert (d.progress.active_lines, d.progress.delivered_lines) == (3, 1)
