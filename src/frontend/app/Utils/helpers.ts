import { ChartData, ChartRange } from '@app/Types';
import { isDigit } from 'json5/lib/util';

export const listToDict = (list: object[], key: string = 'key'): Record<string | number, object> => {
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

export const deepClone = (object: object): object => {
  return JSON.parse(JSON.stringify(object));
};

export const formatChartDate = (range: ChartRange, value: Date | string): string => {
  switch (range) {
    case 'hour': {
      const _d = new Date(value);
      const hour = _d.toLocaleString('default', { hour: '2-digit' });
      return `${hour}`;
    }
    case 'day': {
      const _d = new Date(value);
      const day = _d.toLocaleString('default', { day: '2-digit' });
      const month = _d.toLocaleString('default', { month: 'short' });
      return `${day} ${month}`;
    }
    case 'month': {
      const _d = new Date(value);
      const month = _d.toLocaleString('default', { month: 'short' });
      const year = _d.toLocaleString('default', { year: 'numeric' });
      return `${month} ${year}`;
    }
    case 'year': {
      const _d = new Date(value);
      const year = _d.toLocaleString('default', { year: 'numeric' });
      return `${year}`;
    }
    default:
      return value.toString();
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

export const formatCurrency = (value: number | string | undefined | null): string => {
  if (value === undefined || value === null) {
    return '';
  }

  if (typeof value === 'string' && isDigit(value)) {
    value = parseFloat(value);
  }

  return value.toLocaleString('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });
};
