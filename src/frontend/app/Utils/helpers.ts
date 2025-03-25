import { ChartData, ChartRange } from '@app/Types';
import { isDigit } from 'json5/lib/util';

export const listToDict = (list: object[], key: string = 'key'): Record<string | number, object> | {} => {
  return list?.length
    ? list.reduce((map: Record<string | number, object>, item: object) => {
        const _key = item?.[key];
        if (_key) {
          map[_key] = item;
        }
        return map;
      }, {})
    : {};
};

export const deepClone = (object: object): object | object[] => {
  return JSON.parse(JSON.stringify(object));
};

export const formatChartDate = (range: ChartRange, value: Date | string): string => {
  switch (range) {
    case 'hour': {
      const _d = new Date(value);
      const hour = _d.toLocaleString('default', { hour: '2-digit', timeZone: 'UTC' });
      return `${hour}`;
    }
    case 'day': {
      const _d = new Date(value);
      const day = _d.toLocaleString('default', { day: '2-digit', timeZone: 'UTC' });
      const month = _d.toLocaleString('default', { month: 'short', timeZone: 'UTC' });
      return `${day} ${month}`;
    }
    case 'month': {
      const _d = new Date(value);
      const month = _d.toLocaleString('default', { month: 'short', timeZone: 'UTC' });
      const year = _d.toLocaleString('default', { year: 'numeric', timeZone: 'UTC' });
      return `${month} ${year}`;
    }
    case 'year': {
      const _d = new Date(value);
      const year = _d.toLocaleString('default', { year: 'numeric', timeZone: 'UTC' });
      return `${year}`;
    }
    default: {
      return value.toString();
    }
  }
};

export const generateChartTicks = (maxValue: number) => {
  const numTicks = 10;
  if (maxValue < 10) {
    return Array.from({ length: numTicks }, (_, i) => i + 1);
  }
  const step = Math.ceil(maxValue / numTicks);
  const ticks: number[] = [];
  for (let i = step; i <= maxValue; i += step) {
    ticks.push(i);
  }
  return ticks;
};

export const maxChartValue = (value: number | null | undefined) => {
  if (!value || isNaN(value) || value < 10) {
    return 10;
  }
  if (value > 10000) {
    return Math.ceil(value / 1000) * 1000 + 1000;
  }
  const k = Math.floor(Math.log10(value));
  return Math.floor((value + 10 ** k) / 10 ** k) * 10 ** k;
};

export const generateChartData = (data: ChartData) => {
  const range = data?.range;
  const items: { x: string; y: number }[] = [];
  let maxValue: number = 0;
  if (data?.items?.length && range) {
    data.items.forEach((item) => {
      const y = item.y;
      const x = formatChartDate(range, item.x);
      if (y > maxValue) {
        maxValue = y;
      }
      items.push({
        x: x,
        y: y,
      });
    });
  }
  const roundedMaxValue = maxChartValue(maxValue);
  const tickValues = generateChartTicks(roundedMaxValue);
  return {
    items: items,
    tickValues: tickValues,
    range: range,
    maxValue: roundedMaxValue,
  };
};

export const formatCurrency = (value: number | string | undefined | null, currencySign: string): string => {
  const retval = formatNumber(value, 2);
  if (retval?.length) {
    return (currencySign ? currencySign : '') + retval;
  }
  return retval;
};

export const formatNumber = (value: number | string | undefined | null, decimalPlaces = 0): string => {
  if (value === undefined || value === null) {
    return '';
  }

  if (typeof value === 'string' && isDigit(value)) {
    value = parseFloat(value);
  }

  return value.toLocaleString('en-US', {
    minimumFractionDigits: decimalPlaces,
    maximumFractionDigits: decimalPlaces,
  });
};

export const formatDateTimeToDate = (value: Date | string | undefined): string => {
  if (!value) {
    return '';
  }
  let _d: Date;

  if (typeof value === 'string') {
    _d = new Date(value);
  } else {
    _d = value;
  }

  return new Date(_d.getTime() - _d.getTimezoneOffset() * 60000).toISOString().split('T')[0];
};
