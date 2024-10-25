    def select_report_options(self):
            """Seleciona opções do relatório com verificação mais rigorosa de carregamento."""
            try:
                print("Selecionando 'Relatório com Detalhes'...")
                self.page.click("text=Relatório com Detalhes")

                print("Aguardando elementos carregarem...")
                self.page.wait_for_timeout(2000)
                self.page.wait_for_selector(
                    "input[id*='ctl00'][id*='wtContent']", state="visible", timeout=10000
                )
                
                # Aguarda carregamento completo antes de prosseguir
                if not self.wait_for_loading_complete(timeout=90000):
                    raise Exception("Timeout aguardando carregamento após selecionar relatório detalhado")

                # Mantido o JavaScript original que foi testado e validado
                success = self.page.evaluate("""() => {
                    try {
                        const checkboxesToCheck = ['ctl00', 'ctl04', 'ctl08', 'ctl02', 'ctl06', 'ctl10'];
                        const checkboxesToUncheck = ['ctl12'];
                        
                        const triggerEvents = (element) => {
                            const events = ['change', 'click', 'input'];
                            events.forEach(eventType => {
                                const event = new Event(eventType, { bubbles: true, cancelable: true });
                                element.dispatchEvent(event);
                            });
                        };
                        
                        const handleCheckboxes = (idList, checked) => {
                            idList.forEach(id => {
                                const checkbox = document.querySelector(`input[id*='${id}'][id*='wtContent']`);
                                if (checkbox) {
                                    checkbox.checked = false;
                                    triggerEvents(checkbox);
                                    
                                    if (checked) {
                                        setTimeout(() => {
                                            checkbox.checked = true;
                                            triggerEvents(checkbox);
                                        }, 100);
                                    }
                                }
                            });
                        };
                        
                        handleCheckboxes([...checkboxesToCheck, ...checkboxesToUncheck], false);
                        
                        setTimeout(() => {
                            handleCheckboxes(checkboxesToCheck, true);
                        }, 200);
                        
                        return true;
                    } catch (error) {
                        console.error('Erro ao selecionar checkboxes:', error);
                        return false;
                    }
                }""")

                if not success:
                    raise Exception("Falha ao selecionar opções via JavaScript")

                # Aguarda processamento dos checkboxes
                self.page.wait_for_timeout(1000)
                
                # Aguarda carregamento completo após marcar os checkboxes
                if not self.wait_for_loading_complete(timeout=90000):
                    raise Exception("Timeout aguardando carregamento após marcar checkboxes")

                print("Todas as opções do relatório foram configuradas corretamente.")

            except Exception as e:
                print(f"Erro ao configurar opções do relatório: {e}")
                self.page.screenshot(path="report_options_error.png")
                raise