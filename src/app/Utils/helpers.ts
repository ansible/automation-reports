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
