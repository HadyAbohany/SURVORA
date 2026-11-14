"""Normalize bounded, explicitly requested NASA observations outside the text index."""
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from math import isfinite
from urllib.parse import urlsplit

import httpx

from .knowledge import Observation

DONKI = 'https://ccmc.gsfc.nasa.gov/DONKI-API/get/'
RADLAB = 'https://visualization.osdr.nasa.gov/radlab/api/'
EVENT_FIELDS = {
    'FLR': ('flrID', 'beginTime', 'Solar flare'),
    'CME': ('activityID', 'startTime', 'Coronal mass ejection'),
    'SEP': ('sepID', 'eventTime', 'Solar energetic particle event'),
}


@dataclass(frozen=True)
class RadiationReading(Observation):
    spacecraft: str
    instrument_id: str
    absorbed_dose_rate: float
    unit: str = 'μGy/hour'


def _time(raw, *, implicit_utc=False):
    timestamp = datetime.fromisoformat(raw)
    if timestamp.utcoffset() is None:
        if not implicit_utc:
            raise ValueError('Missing observation timezone')
        timestamp = timestamp.replace(tzinfo=timezone.utc)
    return timestamp.astimezone(timezone.utc)


def _text(value):
    if not isinstance(value, str) or not value.strip():
        raise ValueError('Missing identifier')
    return value


class DonkiSource:
    def fetch(self, client: httpx.Client, kind: str, start: date, end: date):
        if not timedelta(0) <= end - start <= timedelta(days=7):
            raise ValueError('DONKI requires a date window of at most seven days')
        if kind not in EVENT_FIELDS:
            raise ValueError('Unsupported DONKI event kind')
        response = client.get(DONKI + kind, params={
            'startDate': start.isoformat(), 'endDate': end.isoformat(),
        }, timeout=12)
        response.raise_for_status()
        return self.parse(kind, response.json(), datetime.now(timezone.utc))

    @staticmethod
    def parse(kind, payload, retrieved_at):
        if kind not in EVENT_FIELDS or not isinstance(payload, list):
            raise ValueError('Expected a supported DONKI event array')
        id_key, time_key, description = EVENT_FIELDS[kind]
        records = {}
        for row in payload:
            if not isinstance(row, dict):
                raise ValueError('Invalid DONKI event')
            record_id = _text(row.get(id_key))
            link = urlsplit(_text(row.get('link')))
            if link.scheme != 'https' or link.hostname != 'ccmc.gsfc.nasa.gov':
                raise ValueError('Invalid DONKI provenance URL')
            record = Observation(record_id, _time(_text(row.get(time_key))), retrieved_at,
                                 link.geturl(), description)
            version = row.get('versionId')
            if type(version) is not int or version < 1:
                raise ValueError('Invalid DONKI event version')
            if record_id not in records or records[record_id][0] < version:
                records[record_id] = (version, record)
        return [record for _, record in records.values()]


class RadLabSource:
    """Scoped to ISS DosTel absorbed dose rate, using the API's UTC time axis."""
    def fetch(self, client: httpx.Client, start: datetime, end: datetime):
        if any(value.utcoffset() is None for value in (start, end)):
            raise ValueError('RadLab window requires timezone-aware timestamps')
        if not timedelta(0) < end - start <= timedelta(hours=1):
            raise ValueError('RadLab window must be positive and at most one hour')
        start, end = (t.astimezone(timezone.utc).replace(tzinfo=None).isoformat() for t in (start, end))
        response = client.get(RADLAB, params={
            'spacecraft': 'ISS', 'instrument': 'DosTel', 'timestamp>': start,
            'timestamp<': end, 'absorbed_dose_rate': '', 'format': 'json',
        }, timeout=12)
        response.raise_for_status()
        return self.parse(response.json(), datetime.now(timezone.utc), str(response.request.url))

    @staticmethod
    def parse(payload, retrieved_at, source_url=RADLAB):
        required = {'timestamp', 'instrument_id', 'spacecraft', 'absorbed_dose_rate'}
        if not isinstance(payload, dict):
            raise ValueError('Expected a RadLab JSON table')
        columns, rows = payload.get('columns'), payload.get('data')
        if not isinstance(columns, list) or not isinstance(rows, list) or not required.issubset(columns):
            raise ValueError('Missing RadLab measurement columns')
        records = {}
        for row in rows:
            if not isinstance(row, list) or len(row) != len(columns):
                raise ValueError('Invalid RadLab measurement row')
            fields = dict(zip(columns, row))
            value = fields['absorbed_dose_rate']
            if value is None:
                continue
            if type(value) not in (int, float) or not isfinite(value) or value < 0:
                raise ValueError('Invalid absorbed dose rate')
            spacecraft, instrument = fields['spacecraft'], fields['instrument_id']
            if spacecraft != 'ISS' or instrument not in ('DosTel1', 'DosTel2'):
                raise ValueError('Measurement is outside the ISS DosTel adapter scope')
            observed = _time(_text(fields['timestamp']), implicit_utc=True)
            record_id = f'{spacecraft}:{instrument}:{observed.isoformat()}'
            record = RadiationReading(record_id, observed, retrieved_at, source_url,
                                      'ISS orbital absorbed dose rate', spacecraft, instrument, value)
            if record_id in records and records[record_id] != record:
                raise ValueError('Conflicting RadLab measurements')
            records[record_id] = record
        return list(records.values())
