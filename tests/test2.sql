SELECT yes, nom, ta, nie, nonie
, pp, oo, ioijf, vuiw, qenuicr
, nom, ta, nie, nonie, pp
, oo, ioijf, vuiw, qenuicr, nom
, ta, nie, nonie, pp, oo
, ioijf, vuiw, qenuicr, nom, ta
, nie, nonie, pp, oo, ioijf
, vuiw, qenuicr
FROM database_ale_nwm
JOIN d2
ON da.pl = d2.pl

WHERE AVG(pp) > 6723
AND yes <> ta;
