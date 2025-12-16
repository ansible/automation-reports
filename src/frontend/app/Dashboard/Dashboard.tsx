import * as React from 'react';
import { Filters, Header, useToaster } from '@app/Components';
import '@patternfly/react-styles/css/utilities/Spacing/spacing.css';
import '@patternfly/react-styles/css/utilities/Sizing/sizing.css';
import '@patternfly/react-styles/css/utilities/Text/text.css';
import '@patternfly/react-styles/css/utilities/Flex/flex.css';
import {
  Alert,
  Button,
  Flex,
  FlexItem,
  Grid,
  GridItem,
  HelperText,
  HelperTextItem,
  Modal,
  ModalBody,
  ModalFooter,
  ModalHeader,
  Spinner,
  Toolbar,
  ToolbarItem,
} from '@patternfly/react-core';
import { RestService } from '@app/Services';
import { deepClone, getErrorMessage, svgToPng } from '@app/Utils';
import {
  ColumnProps,
  OrderingParams,
  PaginationParams,
  ReportDetail,
  RequestFilter,
  TableResponse,
  TableResult,
  UrlParams,
} from '@app/Types';
import ErrorState from '@patternfly/react-component-groups/dist/dynamic/ErrorState';
import {
  DashboardBarChart,
  DashboardLineChart,
  DashboardTable,
  DashboardTopTable,
  DashboardTotalCards,
} from '@app/Dashboard';
import { CurrencySelector } from '@app/Components';

import useFilterStore from '@app/Store/filterStore';
import useCommonStore from '@app/Store/commonStore';
import { useAutomatedProcessCost, useFilterRetrieveError, useManualCostAutomation } from '@app/Store/filterSelectors';
import { useAuthStore } from '@app/Store/authStore';
import { toasterFromError, ToasterProvider, toasterSuccessMsg } from '@app/Components/Toaster';

const refreshInterval: string = import.meta.env.DATA_REFRESH_INTERVAL_SECONDS
  ? import.meta.env.DATA_REFRESH_INTERVAL_SECONDS
  : '60';

const Dashboard: React.FunctionComponent = () => {
  const filterError = useFilterRetrieveError();
  const [tableData, setTableData] = React.useState<TableResponse>({ count: 0, results: [] } as TableResponse);
  const [detailData, setDetailData] = React.useState<ReportDetail>({} as ReportDetail);
  const [loadDataError, setLoadDataError] = React.useState<boolean>(false);
  const [loading, setLoading] = React.useState<boolean>(true);
  const [pdfLoading, setPdfLoading] = React.useState<boolean>(false);
  const [tableLoading, setTableLoading] = React.useState<boolean>(true);
  const [requestParams, setRequestParams] = React.useState<RequestFilter>();
  const [paginationParams, setPaginationParams] = React.useState<PaginationParams>({
    page: 1,
    page_size: 10,
  } as PaginationParams);
  const [ordering, setOrdering] = React.useState<string>('name');
  const hourly_manual_costs = useManualCostAutomation();
  const hourly_automated_process_costs = useAutomatedProcessCost();
  const interval = React.useRef<number | undefined>(undefined);
  const requestParamsData = React.useRef<RequestFilter>(requestParams as RequestFilter);
  const controller = React.useRef<AbortController | undefined>(undefined);
  const detailController = React.useRef<AbortController | undefined>(undefined);
  const containerLineRefChart = React.useRef<HTMLDivElement>(null);
  const logErrorMessage = useAuthStore((state) => state.logErrorMessage);
  const saveEnableTemplateCreationTime = useCommonStore((state) => state.saveEnableTemplateCreationTime);
  const setAutomatedProcessCost = useFilterStore((state) => state.setAutomatedProcessCostPerMinute);
  const setManualProcessCost = useFilterStore((state) => state.setManualProcessCostPerHour);
  const maxPDFJobTemplates = useFilterStore((state) => state.max_pdf_job_templates);
  const reloadData = useFilterStore((state) => state.reloadData);
  const setReloadData = useFilterStore((state) => state.setReloadData);
  const toaster = useToaster();
  const handelError = (error: unknown) => {
    if (error?.['name'] !== 'CanceledError') {
      setLoading(false);
      setTableLoading(false);
      toaster.add(toasterFromError(error));
    }
  };
  const [isPDFWarningModalOpen, setPDFWarningModalOpen] = React.useState<boolean>(false);

  const fetchServerReportDetails = (signal: AbortSignal) => {
    if (!requestParams) {
      return;
    }
    RestService.fetchReportDetails(signal, requestParams)
      .then((response) => {
        setDetailData(response);
        afterDataRetrieve();
        setLoading(false);
      })
      .catch((e) => {
        const msg = 'Something went wrong while retrieving report details. ' + getErrorMessage(e);
        handelError({name: e.name, message: msg});
      });
  };

  const fetchServerTableData = (fetchDetails: boolean, useLoader: boolean = true) => {
    if (interval.current) {
      clearTimeout();

      detailController.current = new AbortController();
    }
    if (!controller.current) {
      controller.current = new AbortController();
    }

    if (useLoader) {
      if (fetchDetails) {
        setLoading(true);
      } else {
        setTableLoading(true);
      }
    }

    RestService.fetchReports(controller.current.signal, {
      ...requestParams,
      ...paginationParams,
      ...{ ordering: ordering },
    } as UrlParams)
      .then((tableResponse) => {
        setTableData(tableResponse);
        setTableLoading(false);
        if (fetchDetails) {
          if (!detailController.current) {
            detailController.current = new AbortController();
          }
          fetchServerReportDetails(detailController.current.signal);
        } else {
          afterDataRetrieve();
          setLoading(false);
        }
      })
      .catch((e) => {
        const msg = 'Something went wrong while retrieving report data. ' + getErrorMessage(e);
        handelError({name: e.name, message: msg});
      });
  };

  const afterDataRetrieve = () => {
    interval.current = window.setTimeout(
      () => {
        fetchServerTableData(true, false);
      },
      parseInt(refreshInterval) * 1000,
    );
  };

  const clearTimeout = () => {
    controller.current?.abort();
    controller.current = undefined;
    detailController.current?.abort();
    detailController.current = undefined;
    if (interval.current) {
      window.clearTimeout(interval.current);
      interval.current = undefined;
    }
  };

  React.useEffect(() => {
    if (!requestParams) {
      return;
    }
    clearTimeout();
    controller.current = new AbortController();
    detailController.current = new AbortController();
    const fetchDetails = requestParamsData.current !== requestParams;
    fetchServerTableData(fetchDetails);
    requestParamsData.current = requestParams;
    return () => {
      controller.current?.abort();
      detailController.current?.abort();
    };
  }, [requestParams, paginationParams, ordering]);

  React.useEffect(() => {
    if (reloadData) {
      clearTimeout();
      fetchServerTableData(true);
      setReloadData(false);
    }
  }, [reloadData]);

  const costChanged = (type: string, value: number) => {
    const oldValue = type === 'manual' ? hourly_manual_costs : hourly_automated_process_costs;
    if (oldValue !== value) {
      clearTimeout();
      setLoading(true);
      value = Number(value.toFixed(2));
      let msg =
        type === 'manual'
          ? 'Average cost of per minute to manually run the job'
          : 'Average cost per minute of running on AAP';
      RestService.updateCosts({ type: type, value: value })
        .then(() => {
          msg += ' updated successfully.';
          toaster.add(toasterSuccessMsg(msg));
          fetchServerTableData(true, false);
          if (type === 'manual') {
            setManualProcessCost(value);
          } else {
            setAutomatedProcessCost(value);
          }
        })
        .catch((e) => {
          const errorMsg = 'Failed to update ' + msg + '. ' + getErrorMessage(e);
          handelError({name: e?.name, message: errorMsg});
        });
    } else {
      afterDataRetrieve();
    }
  };

  const onItemEdit = (newValue: TableResult, oldValue: TableResult) => {
    let manually_minutes = newValue.time_taken_manually_execute_minutes;
    let automation_minutes = newValue.time_taken_create_automation_minutes;

    manually_minutes = typeof manually_minutes === 'string' ? parseFloat(manually_minutes) : manually_minutes;

    automation_minutes = typeof automation_minutes === 'string' ? parseFloat(automation_minutes) : automation_minutes;

    if (
      oldValue.time_taken_manually_execute_minutes === manually_minutes &&
      oldValue.time_taken_create_automation_minutes === automation_minutes
    ) {
      afterDataRetrieve();
      return;
    }
    clearTimeout();
    setLoading(true);
    const newItem = deepClone(newValue) as TableResult;
    newItem.time_taken_manually_execute_minutes = Math.round(manually_minutes);
    newItem.time_taken_create_automation_minutes = Math.round(automation_minutes);
    const msg = 'Template ' + newItem.name;
    RestService.updateTemplate(newItem)
      .then(() => {
        fetchServerTableData(true, false);
        toaster.add(toasterSuccessMsg(msg + ' updated successfully.'));
      })
      .catch((e) => {
        const errorMsg = 'Failed to update ' + msg + '. ' + getErrorMessage(e);
        handelError({name: e?.name, message: errorMsg});
      });
  };

  const filtersChange = (requestFilter: RequestFilter) => {
    setPaginationParams({ page: 1, page_size: paginationParams.page_size });
    setRequestParams(requestFilter);
  };

  const onPaginationChange = (pagination: PaginationParams) => {
    setPaginationParams(pagination);
  };

  const onSortChange = (ordering: string) => {
    setPaginationParams({ page: 1, page_size: paginationParams.page_size });
    setOrdering(ordering);
  };

  const topProjectColumns: ColumnProps[] = [
    {
      name: 'project_name',
      title: 'Project name',
      isVisible: true,
    },
    {
      name: 'count',
      title: 'Total no. of jobs',
      type: 'number',
      isVisible: true,
    },
  ];

  const topUsersColumns: ColumnProps[] = [
    {
      name: 'user_name',
      title: 'User name',
      isVisible: true,
    },
    {
      name: 'count',
      title: 'Total no. of jobs',
      type: 'number',
      isVisible: true,
    },
  ];

  const onInputFocus = () => {
    clearTimeout();
  };

  const exportToCsv = () => {
    setTableLoading(true);
    RestService.exportToCSV({ ...requestParams, ...{ ordering: ordering } } as RequestFilter & OrderingParams)
      .then(() => {
        setTableLoading(false);
      })
      .catch((e) => {
        const errorMsg = 'Something went wrong while exporting CSV. Please try again later.';
        handelError({name: e?.name, message: errorMsg});
      });
  };

  const pdfDownload = async () => {
    const jobsChartSvg = document.querySelector('.jobs-chart')?.querySelector('svg');
    const jobsChartPng = await svgToPng(jobsChartSvg);

    const hostChartSvg = document.querySelector('.host-chart')?.querySelector('svg');
    const hostChartPng = await svgToPng(hostChartSvg);

    RestService.exportToPDF(
      { ...requestParams, ...{ ordering: ordering } } as RequestFilter & OrderingParams,
      jobsChartPng,
      hostChartPng,
    )
      .catch((e) => {
        const errorMsg = 'Something went wrong while exporting PDF. Please try again later.';
        handelError({name: e?.name, message: errorMsg});
      })
      .finally(() => {
        setPdfLoading(false);
      });
  };

  const onPdfBtnClick = () => {
    if (tableData.count > maxPDFJobTemplates) {
      setPDFWarningModalOpen(true);
    } else {
      setPdfLoading(true);
      setTimeout(pdfDownload, 150);
    }
  };

  const onEnableTemplateCreationTimeChange = async (checked: boolean) => {
    clearTimeout();
    setLoading(true);
    saveEnableTemplateCreationTime(checked)
      .then(() => {
        toaster.add(
          toasterSuccessMsg('Include time taken to create automation into calculation updated successfully.'),
        );
        fetchServerTableData(true, true);
      })
      .catch((e) => {
        handelError(e);
      });
  };

  const topUsersToolTip = (
    <div>
      <div>
        This section lists the top five users of Ansible Automation Platform, with a breakdown of the total number of
        jobs run by each user.
      </div>
      <ul>
        <br />
        <li>
          <strong>○ NOTE:</strong> Scheduled jobs can affect these results, because they do not represent a real,
          logged-in user.
        </li>
      </ul>
    </div>
  );

  const pdfModalTitle = (
    <HelperText>
      <HelperTextItem variant="error" style={{ fontSize: '20px' }}>
        PDF Download Failed: Data Volume Exceeded
      </HelperTextItem>
    </HelperText>
  );

  const pdfWarningModal = (
    <Modal
      isOpen={isPDFWarningModalOpen}
      ouiaId="DFWarningModal"
      aria-labelledby="pdf-warning-modal-title"
      aria-describedby="pdf-warning-modal-body"
      variant={'small'}
    >
      <ModalHeader title={pdfModalTitle} labelId="pdf-warning-modal-title" />
      <ModalBody id="pdf-warning-modal-body">
        <HelperText style={{ fontSize: '14px' }}>
          <HelperTextItem variant={'default'}>
            We were unable to generate your PDF because the selected report exceeds the maximum record limit.
          </HelperTextItem>
          <HelperTextItem variant={'default'}>
            Please apply additional filters to narrow your data and retry.
          </HelperTextItem>
        </HelperText>
      </ModalBody>
      <ModalFooter>
        <Button
          key="close"
          variant="link"
          onClick={() => {
            setPDFWarningModalOpen(false);
          }}
        >
          Close
        </Button>
      </ModalFooter>
    </Modal>
  );

  // @ts-ignore
  return (
    <div>
      <Header
        title={'Automation Dashboard'}
        subtitle={
          'Discover the significant cost and time savings achieved by automating Ansible jobs with the Ansible Automation Platform. Explore how automation reduces manual effort, enhances efficiency, and optimizes IT operations across your organization.'
        }
        pdfBtnText={
          !loadDataError && !filterError && !logErrorMessage && !loading && !pdfLoading && tableData?.count > 0
            ? 'Save as PDF'
            : undefined
        }
        onPdfBtnClick={onPdfBtnClick}
      ></Header>
      {(loadDataError || filterError) && !logErrorMessage && (
        <div className={'error'}>
          <ErrorState
            titleText="Something went wrong"
            bodyText="Please contact your system administrator."
            customFooter="&nbsp;"
            headingLevel={'h1'}
            variant={'full'}
          />
        </div>
      )}

      {logErrorMessage && (
        <div className={'main-layout'}>
          <Alert variant="danger" isInline title={logErrorMessage} />
        </div>
      )}
      {!loadDataError && !filterError && !logErrorMessage && (
        <div className={'main-layout'}>
          {pdfWarningModal}
          {(loading || pdfLoading) && (
            <div className={'loader'}>
              <Spinner className={'spinner'} diameter="80px" aria-label="Loader" />
            </div>
          )}

          <Flex className="pf-m-gap-none">
            <FlexItem>
              <Filters onChange={filtersChange}></Filters>
            </FlexItem>
            <FlexItem align={{ default: 'alignLeft', '2xl': 'alignRight' }} className="currency-selector">
              <Toolbar>
                <ToolbarItem>
                  <CurrencySelector></CurrencySelector>
                </ToolbarItem>
              </Toolbar>
            </FlexItem>
          </Flex>

          <div>
            <Grid hasGutter>
              <GridItem className="pf-m-12-col pf-m-8-col-on-2xl pf-m-9-col-on-3xl pf-m-10-col-on-4xl pf-v6-l-grid pf-m-gutter">
                <DashboardTotalCards data={detailData}></DashboardTotalCards>
                <Grid hasGutter>
                  <GridItem className="pf-m-12-col pf-m-6-col-on-md" style={{ height: '100%' }}>
                    <div ref={containerLineRefChart}>
                      <DashboardLineChart
                        value={detailData?.total_number_of_job_runs?.value as number}
                        chartData={detailData.job_chart}
                        loading={loading}
                      ></DashboardLineChart>
                    </div>
                  </GridItem>
                  <GridItem className="pf-m-12-col pf-m-6-col-on-md" style={{ height: '100%' }}>
                    <DashboardBarChart
                      value={detailData?.total_number_of_host_job_runs?.value as number}
                      chartData={detailData?.host_chart}
                      loading={loading}
                    ></DashboardBarChart>
                  </GridItem>
                </Grid>
              </GridItem>

              <GridItem className="pf-m-12-col-on-lg pf-m-4-col-on-2xl pf-m-3-col-on-3xl pf-m-2-col-on-4xl">
                <Grid hasGutter style={{ height: '100%' }}>
                  <GridItem className="pf-m-12-col pf-m-6-col-on-md pf-m-12-col-on-2xl" style={{ height: '100%' }}>
                    <div style={{ height: '100%' }}>
                      <DashboardTopTable
                        title={'Top 5 projects'}
                        tooltip={
                          'This section lists the top five automation projects based on the number of jobs executed.'
                        }
                        infoIcon={true}
                        columns={topProjectColumns}
                        data={detailData?.projects ? detailData.projects : []}
                      ></DashboardTopTable>
                    </div>
                  </GridItem>
                  <GridItem className="pf-m-12-col pf-m-6-col-on-md pf-m-12-col-on-2xl" style={{ height: '100%' }}>
                    <div style={{ height: '100%' }}>
                      <DashboardTopTable
                        title={'Top 5 users'}
                        tooltip={topUsersToolTip}
                        infoIcon={true}
                        columns={topUsersColumns}
                        data={detailData?.users ? detailData.users : []}
                      ></DashboardTopTable>
                    </div>
                  </GridItem>
                </Grid>
              </GridItem>
            </Grid>
          </div>
          <div className="pf-v6-u-mt-xl">
            <DashboardTable
              data={tableData}
              onCostChanged={costChanged}
              totalSaving={detailData?.total_saving}
              costOfAutomatedExecution={detailData.cost_of_automated_execution}
              costOfManualAutomation={detailData.cost_of_manual_automation}
              totalTimeSavings={detailData.total_time_saving}
              onPaginationChange={onPaginationChange}
              onSortChange={onSortChange}
              pagination={paginationParams}
              onItemEdit={onItemEdit}
              loading={tableLoading}
              onInputFocus={onInputFocus}
              onExportCsv={exportToCsv}
              onEnableTemplateCreationTimeChange={onEnableTemplateCreationTimeChange}
            ></DashboardTable>
          </div>
        </div>
      )}
    </div>
  );
};

export { Dashboard };
